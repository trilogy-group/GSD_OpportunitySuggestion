import json


import crm_services
import rank_services


def lambda_handler(event, context) -> dict:
    body = json.loads(event['body'])

    print(body)

    data = body.get('data')
    if not data:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Missing required parameters: data is required'
            })
        }
    
    config = body.get('config', {})

    transcript = data.get('transcript')
    user_ids = data.get('user_ids')
    account_id = data.get('account_id')
    product_ids = data.get('product_ids')

    if not transcript or not account_id:
        print('Missing required parameters: transcript, account_id are required')
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Missing required parameters: transcript, account_id are required'
            })
        }
    
    if not config.get('crm_platform') or not config.get('access_token'):
        print('Missing required parameters: crm_platform, access_token are required')
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Missing required parameters: crm_platform, access_token are required'
            })
        }
    
    crm_platform = config.get('crm_platform')
    
    if crm_platform == 'salesforce':
        crm_service = crm_services.SalesforceService(config)
        rank_service = rank_services.SalesforceRank()
    elif crm_platform == 'pivotal':
        if not config.get('form_name') or not config.get('pivotal_environment_name'):
            print('Missing required parameters: form_name and pivotal_environment_name are required')
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters: form_name and pivotal_environment_name are required'
                })
            }

        crm_service = crm_services.PivotalService(config)
        rank_service = rank_services.PivotalRank()
    elif crm_platform == 'acrm':
        user_credentials = config.get('access_token', '').split(':')
        if len(user_credentials) != 2:
            print('Invalid access token format. Format should be username:password')
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid access token format. Format should be username:password'
                })
            }

        config['username'] = user_credentials[0]
        config['password'] = user_credentials[1]
        crm_service = crm_services.ACRMService(config)
        rank_service = rank_services.ACRMRank()
    else:
        print('Invalid CRM platform. Valid platforms are salesforce, pivotal, acrm')
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Invalid CRM platform. Valid platforms are salesforce, pivotal, acrm'
            })
        }

    # Get opportunity products
    raw_opportunity_products = crm_service.get_opportunity_products(user_ids, account_id, product_ids, format = True)
    opportunity_products = []

    if raw_opportunity_products:  # Only process products if we got them successfully
        for opportunity_product in raw_opportunity_products:
            opportunity_products.append({
                'id': opportunity_product.get('Id'),
                'opportunity_id': opportunity_product.get('OpportunityId'),
                'product_id': opportunity_product.get('Product2Id'),
                'product_name': opportunity_product.get('Product2').get('Name'),
                'quantity': opportunity_product.get('Quantity')
            })

    # Get opportunities assigned to users
    raw_opportunities = crm_service.get_opportunities_by_account_id(account_id, format = True)
    opportunities = []
    
    # Get opportunity products for each opportunity
    opportunity_products_map = {}
    for op in opportunity_products:
        opp_id = op['opportunity_id']
        if opp_id not in opportunity_products_map:
            opportunity_products_map[opp_id] = []
        opportunity_products_map[opp_id].append(op)
    
    for opportunity in raw_opportunities:
        # Pass empty list if no products were found for this opportunity
        opp_products = opportunity_products_map.get(opportunity.get('Id'), [])
        opportunity_rank = rank_service.rank_opportunity_score(
            opportunity,
            opp_products,  # This will be empty if products request failed
            transcript,
            user_ids
        )
        opportunity_to_be_added = {
            'id': opportunity.get('Id'),
            'name': opportunity.get('Name'),
            'stage_name': opportunity.get('StageName'),
            'owner_id': opportunity.get('OwnerId'),
            'rank': opportunity_rank
        }
        opportunities.append(opportunity_to_be_added)

    # Sort opportunities by rank in descending order
    opportunities.sort(key=lambda x: x['rank'], reverse=True)
    
    # Filter out opportunities with score lower than 0.5
    opportunities = [opp for opp in opportunities if opp['rank'] >= 0.5]
    
    # Only apply suggestion logic if we have opportunities left
    if opportunities:
        opportunities = rank_service.determine_suggestion(
            opportunities,
            min_score_threshold=0.25,
            score_difference_threshold=0.1
        )
    
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'result': opportunities,
            'error': None,
            'metadata': {
                'min_score_threshold': 0.5,  # Updated to reflect new minimum score
                'score_difference_threshold': 0.1
            }
        })
    }
    
    print(response)

    return response
