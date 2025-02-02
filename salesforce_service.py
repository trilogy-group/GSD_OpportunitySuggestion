import requests
import logging
from urllib.parse import urljoin
from typing import Dict


# Configure logging
logger = logging.getLogger(__name__)


AUTH_FIELDS = {
    "url_domain": "https://trilogy-sales.my.salesforce.com"
}


class SalesforceService:
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    def __post_init__(self):
        if self.config and not self.config.get("url_domain"):
            self.config = AUTH_FIELDS
    
    def _perform_query(self, query, format = False):
        url = urljoin(self.config.get("url_domain"), f"services/data/v62.0/query")
        headers = {
            'Authorization': f'Bearer {self.config.get("access_token")}',
            'Content-Type': 'application/json'
        }
        
        logger.debug(f"URL: {url}")
        logger.debug(f"Query: {query}")
        
        response = requests.get(url, headers=headers, params={'q': query})
        
        if response.status_code != 200:
            logger.error(f"Failed to fetch data: {response.status_code} - {response.text}")
            return []
        
        response_json = response.json()
        
        if format:
            return response_json.get('records') if response_json.get('records') else []
        
        return response_json
    
    def get_opportunity_products(self, user_ids, account_id, product_ids = [], format = False):   
        product_filter = ""
        if product_ids:
            quoted_ids = [f"'{id}'" for id in product_ids]
            product_filter = f" AND Product2Id IN ({','.join(quoted_ids)})"
            
        users_filter = ""
        if user_ids:
            quoted_ids = [f"'{id}'" for id in user_ids]
            users_filter = f" AND Opportunity.OwnerId IN ({','.join(quoted_ids)}) "
        
        new_query = f"""
        SELECT Id, OpportunityId, Product2Id, Product2.Name, Quantity
        FROM OpportunityLineItem
        WHERE Opportunity.AccountId = '{account_id}'{users_filter}{product_filter}
        ORDER BY Opportunity.CreatedDate DESC
        """
        try:
            return self._perform_query(new_query, format)
        except Exception as e:
            logger.error(f"Error fetching opportunity products: {e}")
            return []
    
    
    def get_opportunities_by_account_id(self, account_id, format = False):
        opportunity_query = f"""
        SELECT Id, OwnerId, Name, StageName, AccountId, Account.Name, CreatedDate
        FROM Opportunity
        WHERE AccountId = '{account_id}'
        ORDER BY CreatedDate DESC
        """
        try:
            return self._perform_query(opportunity_query, format)
        except Exception as e:
            logger.error(f"Error fetching opportunities by account ID: {e}")
            return []


    def get_opportunities_assigned_to_users(self, user_ids, account_id, format = False):
        users_filter = ""
        if user_ids:
            # Add single quotes around each ID and join them with commas
            quoted_ids = [f"'{id}'" for id in user_ids]
            users_filter = f" AND OwnerId IN ({','.join(quoted_ids)})"
        
        opportunity_query = f"""
        SELECT Id, Name, StageName, AccountId, Account.Name, CreatedDate
        FROM Opportunity
        WHERE AccountId = '{account_id}'{users_filter}
        ORDER BY CreatedDate DESC
        """        
        try:
            return self._perform_query(opportunity_query, format)
        except Exception as e:
            logger.error(f"Error fetching opportunities assigned to users: {e}")
            return []
