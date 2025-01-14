import json
from flask import Flask, render_template, request, jsonify
import logging

import lambda_function


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)


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
