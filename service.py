import csv
import os
import logging


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_products_from_csv(product_ids):
    products = []
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'products.csv')
    with open(csv_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['Id'] in product_ids:
                products.append({
                    'id': row['Id'],
                    'name': row['Name']
                })
    return products


def get_users_from_csv():
    """Get list of users from users.csv"""
    users = []
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    try:
        with open(csv_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            # Return full user objects instead of just emails
            users = list(csv_reader)
            logger.debug(f"Found users: {users}")
        return users
    except Exception as e:
        logger.error(f"Error reading users.csv: {str(e)}")
        return []


def get_user(email):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'users.csv')
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found at: {csv_path}")
        raise FileNotFoundError(f"Users database not found at {csv_path}")
    
    with open(csv_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        headers = csv_reader.fieldnames
        logger.debug(f"CSV headers: {headers}")
        
        if 'Email' not in headers:
            raise Exception("CSV file is missing 'email' column")
        
        # Check if email exists in any row
        for row in csv_reader:
            if row['Email'] == email:
                return row

        return None


def get_user_products(user_ids):
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'users_products.csv')
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Users products database not found at {csv_path}")
    
    products = []
    
    with open(csv_path, 'r') as file:
        csv_reader = csv.DictReader(file)
        headers = csv_reader.fieldnames
        
        if 'UserId' not in headers:
            raise Exception("CSV file is missing 'UserId' column")
        
        # Get the list of products for the user
        for row in csv_reader:
            if row['UserId'] in user_ids:
                products.append(row)
    
    return products
