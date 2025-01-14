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
    salesforce_access_token = data.get('salesforce_access_token')

    if not transcript or not user_ids or not account_id:
        return {
            'error': 'Missing required parameters: transcript, user_id and account_id are required'
        }
        
    opportunities_response = salesforce_service.get_opportunities_assigned_to_users(salesforce_access_token, user_ids, account_id)

    opportunities = opportunities_response.get('records', []) if opportunities_response.get('done') == True else []
    user_products = service.get_user_products(user_ids)
        
    opportunity_scores = []
    for opportunity in opportunities:
        ranked_opportunity = ai_service.rank_opportunity(opportunity, user_products, transcript)
        opportunity_scores.append(ranked_opportunity)

    dummy_response = {
        'result': opportunity_scores,
        'error': None,
        'metadata': {}
    }
    
    return dummy_response, 200
