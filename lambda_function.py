import json

import ai_service
import service
import salesforce_service


def lambda_handler(event, context) -> dict:
    body = json.loads(event['body'])
    data = body['data']

    transcript = data.get('transcript')
    user_ids = data.get('user_ids')
    account_id = data.get('account_id')
    product_ids = data.get('product_ids')
    salesforce_access_token = data.get('salesforce_access_token')
    max_results = data.get('max_results') or 10

    if not transcript or not user_ids or not account_id or not product_ids:
        return {
            'error': 'Missing required parameters: transcript, user_id, account_id and product_ids are required'
        }

    user_products = service.get_products_from_csv(product_ids)

    # Get opportunity products
    raw_opportunity_products = salesforce_service.get_opportunity_products(salesforce_access_token, user_ids, account_id, product_ids, format = True)
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
    raw_opportunities = salesforce_service.get_opportunities_assigned_to_users(salesforce_access_token, user_ids, account_id, format = True)
    opportunities = []
    
    for opportunity in raw_opportunities:
        opportunity_rank = ai_service.rank_opportunity_score(user_products, transcript)
        opportunity_to_be_added = {
            'id': opportunity.get('Id'),
            'name': opportunity.get('Name'),
            'stage_name': opportunity.get('StageName'),
            'rank': opportunity_rank
        }
        opportunities.append(opportunity_to_be_added)

    dummy_response = {
        'result': opportunities,
        'error': None,
        'metadata': {}
    }

    return dummy_response, 200
