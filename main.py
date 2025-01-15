from flask import Flask, request, jsonify
import logging

import ai_service
import lambda_function
import salesforce_service


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/suggestion', methods=['POST'])
def suggestion():
    request_data = request.get_json()
    
    if not request_data:
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
        
    user_ids = request_data.get('user_ids')
    account_id = request_data.get('account_id')
    product_ids = request_data.get('product_ids')
    transcript = request_data.get('transcript')
    salesforce_access_token = request_data.get('salesforce_access_token')
        
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
    
    # Create a map of opportunity products
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
    
    return jsonify({
        'opportunities': opportunities,
        'metadata': {
            'min_score_threshold': 0.25,
            'score_difference_threshold': 0.1
        }
    })
    

@app.route('/opportunities', methods=['POST'])
def get_opportunities_by_user_ids():
    request_data = request.get_json()
    
    if not request_data:
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
    
    user_ids = request_data.get('user_ids')
    account_id = request_data.get('account_id')
    salesforce_access_token = request_data.get('salesforce_access_token')
    
    opportunities = salesforce_service.get_opportunities_assigned_to_users(salesforce_access_token, user_ids, account_id)
    opportunities = opportunities.get('records') if opportunities.get('records') else []
        
    return jsonify({
        'opportunities': opportunities
    })


@app.route('/opportunity_products', methods=['POST'])
def get_opportunity_products():
    request_data = request.get_json()
    
    if not request_data:
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
        
    user_ids = request_data.get('user_ids')
    account_id = request_data.get('account_id')
    product_ids = request_data.get('product_ids')
    salesforce_access_token = request_data.get('salesforce_access_token')
    
    opportunity_products = salesforce_service.get_opportunity_products(salesforce_access_token, user_ids, account_id, product_ids)
    opportunity_products = opportunity_products.get('records') if opportunity_products.get('records') else []
    
    return jsonify({
        'opportunity_products': opportunity_products
    })


@app.route('/opportunity_suggestion', methods=['POST'])
def opportunity_suggestion():
    request_data = request.get_json()
    
    if not request_data or not request_data.get('data'):
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
    
    data = request_data.get('data')
    config = request_data.get('config') or {}

    response = lambda_function.lambda_handler({
        'body': data,
        'config': config
    }, {})
    
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
