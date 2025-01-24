import json

import ai_service
import salesforce_service


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
    salesforce_access_token = data.get('salesforce_access_token')

    if not transcript or not user_ids or not account_id:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Missing required parameters: transcript, user_id, account_id are required'
            })
        }
        
    salesforce_svc = salesforce_service.SalesforceService(config)

    # Get opportunity products
    raw_opportunity_products = salesforce_svc.get_opportunity_products(salesforce_access_token, user_ids, account_id, product_ids, format = True)
    opportunity_products = []

    for opportunity_product in raw_opportunity_products:
        opportunity_products.append({
            'id': opportunity_product.get('Id'),
            'opportunity_id': opportunity_product.get('OpportunityId'),
            'product_id': opportunity_product.get('Product2Id'),
            'product_name': opportunity_product.get('Product2').get('Name'),
            'quantity': opportunity_product.get('Quantity')
        })

    # Get opportunities assigned to users
    raw_opportunities = salesforce_svc.get_opportunities_by_account_id(salesforce_access_token, account_id, format = True)
    opportunities = []
    
    # Get opportunity products for each opportunity
    opportunity_products_map = {}
    for op in opportunity_products:
        opp_id = op['opportunity_id']
        if opp_id not in opportunity_products_map:
            opportunity_products_map[opp_id] = []
        opportunity_products_map[opp_id].append(op)
    
    for opportunity in raw_opportunities:
        opp_products = opportunity_products_map.get(opportunity.get('Id'), [])
        opportunity_rank = ai_service.rank_opportunity_score(
            opportunity,
            opp_products,
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
    
    # Apply suggestion logic
    opportunities = ai_service.determine_suggestion(
        opportunities,
        min_score_threshold=0.25,  # Lowered from 0.3
        score_difference_threshold=0.1  # Lowered from 0.15
    )
    
    response = {
        'statusCode': 200,
        'body': json.dumps({
            'result': opportunities,
            'error': None,
            'metadata': {
                'min_score_threshold': 0.25,
                'score_difference_threshold': 0.1
            }
        })
    }
    
    print(response)

    return response
