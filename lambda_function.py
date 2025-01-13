from flask import Flask, request, jsonify, render_template
import json
import csv
import os
import requests
import logging

import service


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


def get_users_from_csv():
    """Get list of users from users.csv"""
    users = []
    csv_path = os.path.join(os.path.dirname(__file__), 'users.csv')
    try:
        with open(csv_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            users = [row['email'] for row in csv_reader]
        return users
    except Exception as e:
        logger.error(f"Error reading users.csv: {str(e)}")
        return []


@app.route('/', methods=['GET'])
def index():
    users = get_users_from_csv()
    return render_template('index.html', users=users)


@app.route('/submit_form', methods=['POST'])
def submit_form():
    try:
        selected_user = request.form.get('user')
        account_id = request.form.get('account_id')
        
        logger.debug(f"Form submitted - User: {selected_user}, Account ID: {account_id}")
        
        # TODO: Handle form submission
        
        return jsonify({
            'message': 'Form submitted successfully',
            'user': selected_user,
            'account_id': account_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing form submission: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500


@app.route('/opportunity_suggestion', methods=['POST'])
def opportunity_suggestion():
    # ... existing opportunity_suggestion endpoint code ... 