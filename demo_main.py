from flask import Flask, render_template, request, jsonify
import logging

import service
from salesforce_service import authenticate, get_opportunities_assigned_to_user
from langchain_service import Speeds, service as langchain_svc


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    users = service.get_users_from_csv()
    return render_template('index.html', users=users)


@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        selected_user = request.form.get('user')
        account_id = request.form.get('account_id')
        
        logger.debug(f"Form submitted - User: {selected_user}, Account ID: {account_id}")
        
        user = service.get_user(selected_user)
        
        logger.debug(f"User: {user}")
        
        # Validate user email
        if not user:
            return render_template('index.html', 
                                users=service.get_users_from_csv(),
                                error=f'Sales Representative with email {selected_user} not found in the list')
        
        salesforce_access_token = "00D2x000000qNQa!AQUAQEgAmHEQtx64GxtpwcSEnEVTao8EmpvAgOuqVRfew3SPShkJ1UBbhCnx1TcMJS8.ZZdvxhcDJHc5NM0_qx44HIMOru1g"

        opportunities = get_opportunities_assigned_to_user(salesforce_access_token, user['Id'], account_id)
        
        return render_template('index.html',
                             users=service.get_users_from_csv(),
                             selected_user=selected_user,
                             account_id=account_id,
                             opportunities=opportunities.get('records', []))
        
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}")
        return render_template('index.html',
                             users=service.get_users_from_csv(),
                             error=str(e))


@app.route('/opportunity_suggestion', methods=['POST'])
def opportunity_suggestion():
    request_data = request.get_json()
    
    if not request_data or not request_data.get('data') or not request_data.get('config'):
        return jsonify({
            'error': 'Missing JSON body'
        }), 400
    
    data = request_data.get('data')
    config = request_data.get('config')
    
    transcript = data.get('transcript')
    email = data.get('email')
    account_id = data.get('account_id')
    
    dummy_response = {
        'result': [
            { 'id': '1', 'name': 'Opportunity 1', 'score': 0.5 },
            { 'id': '2', 'name': 'Opportunity 2', 'score': 0.5 }
        ],
        'error': None,
        'metadata': {}
    }
    
    return jsonify(dummy_response), 200


@app.route('/opportunity_suggestionx', methods=['POST'])
def opportunity_suggestion_x():
    try:
        # Get parameters from JSON body
        data = request.get_json()
        if not data:
            return jsonify({
                'error': 'Missing JSON body'
            }), 400
            
        transcript = data.get('transcript')
        email = data.get('email')
        account_id = data.get('account_id')
        
        logger.debug(f"Received request - email: {email}, transcript length: {len(transcript) if transcript else 0}")
        
        # Validate input
        if not transcript or not email or not account_id:
            return jsonify({
                'error': 'Missing required parameters: transcript, email and account_id are required'
            }), 400
            
        user = service.get_user(email)
        
        logger.debug(f"User: {user}")
        
        # Validate user email
        if not user:
            return jsonify({
                'error': f'Sales Representative with email {email} not found in the list'
            }), 404
            
        # return authenticate()
        
        salesforce_access_token = "00D2x000000qNQa!AQUAQEgAmHEQtx64GxtpwcSEnEVTao8EmpvAgOuqVRfew3SPShkJ1UBbhCnx1TcMJS8.ZZdvxhcDJHc5NM0_qx44HIMOru1g"
        
        user_products = service.get_user_products(user['Id'])
        opportunities_response = get_opportunities_assigned_to_user(salesforce_access_token, user['Id'], account_id)
        
        if opportunities_response.get('done') == True:
            opportunities = opportunities_response.get('records', [])
        else:
            opportunities = []
        
        prompt = f"""
        You are a senior software engineer.
        Given the following transcript, identify the products that are being discussed.
        
        These are the products that the sales representative is selling:
        {user_products}

        Return a list of product ids that are mentioned in the transcript.
        If no product is mentioned, return an empty list.
        """
        
        products_mentioned = langchain_svc.chat(
            [{ 'role': 'user', 'content': transcript }],
            prompt,
            Speeds.FAST
        )
        
        rank_opportunities_prompt = f"""
        You are a senior software engineer.
        Given the following opportunities, rank them based on the products that are being discussed.
        
        These are the products that the sales representative is selling:
        {user_products}

        Return the augmented opportunities with a score between 0 and 1. Being closer to 1 means the opportunity is more likely to be the one being discussed.
        The response should be a JSON object with the following fields:
        - id: The opportunity id
        - name: The opportunity name
        - score: The score of the opportunity
        These files come from the Salesforce API:
        
        {opportunities}
        """
        
        ranked_opportunities = langchain_svc.chat(
            [{ 'role': 'user', 'content': transcript }],
            rank_opportunities_prompt,
            Speeds.FAST
        )
        
        # Process the transcript (placeholder for future processing)
        
        return jsonify({
            'user_products': user_products,
            'opportunities': ranked_opportunities,
            'products_mentioned': products_mentioned
        }), 200
        
    except Exception as e:
        logger.error(f"Error in opportunity_suggestion: {str(e)}")
        raise e


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
