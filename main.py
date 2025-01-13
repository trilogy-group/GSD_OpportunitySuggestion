from flask import Flask, render_template, request, jsonify
import logging

import service
from salesforce_service import authenticate, get_opportunities_assigned_to_user


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
        
        # salesforce_token = authenticate()
        salesforce_access_token = "00D2x000000qNQa!AQUAQEgAmHEQtx64GxtpwcSEnEVTao8EmpvAgOuqVRfew3SPShkJ1UBbhCnx1TcMJS8.ZZdvxhcDJHc5NM0_qx44HIMOru1g"
        
        # Get user's products
        #products = service.get_user_products(user['Id'])
        opportunities = get_opportunities_assigned_to_user(salesforce_access_token, user['Id'], account_id)
        
        # Process the transcript (placeholder for future processing)
        
        return jsonify({
            'message': 'Transcript processed successfully',
            'email': email,
            'transcript_length': len(transcript),
            'user': user,
            'salesforce_access_token': salesforce_access_token,
            # 'products': products,
            'opportunities': opportunities
        }), 200
        
    except Exception as e:
        logger.error(f"Error in opportunity_suggestion: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
