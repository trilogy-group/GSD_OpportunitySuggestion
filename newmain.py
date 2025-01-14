import json
import random
from flask import Flask, render_template, request, jsonify
import logging

import service
import salesforce_service
from langchain_service import Speeds, service as langchain_svc


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def lambda_handler(event: dict, context: dict = None) -> dict:
    transcript = event.get('transcript')
    user_id = event.get('user_id')
    account_id = event.get('account_id')
    salesforce_access_token = event.get('salesforce_access_token')
    
    if not transcript or not user_id or not account_id:
        return jsonify({
            'error': 'Missing required parameters: transcript, user_id and account_id are required'
        }), 400
        
    opportunities_response = salesforce_service.get_opportunities_assigned_to_user(salesforce_access_token, user_id, account_id)

    opportunities = opportunities_response.get('records', []) if opportunities_response.get('done') == True else []
    user_products = service.get_user_products(user_id)
    
    logger.debug(f"User products: {json.dumps(user_products, indent=4)}")
    
    opportunity_scores = []
    for opportunity in opportunities:
        opportunity_scores.append({
            'id': opportunity.get('Id'),
            'name': opportunity.get('Name'),
            'score': random.random()
        })

    dummy_response = {
        'result': opportunity_scores,
        'error': None,
        'metadata': {}
    }
    
    return dummy_response, 200


@app.route('/opportunity_suggestion', methods=['POST'])
def opportunity_suggestion():
    request_data = request.get_json()
    
    if not request_data or not request_data.get('data'):
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
    
    data = request_data.get('data')
    config = request_data.get('config') or {}

    response = lambda_handler(data, config)
    
    return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
