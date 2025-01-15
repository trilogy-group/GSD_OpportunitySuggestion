import requests
import logging
from urllib.parse import urljoin
from typing import Dict


# Configure logging
logger = logging.getLogger(__name__)


AUTH_FIELDS = {
    "url_domain": "https://trilogy-sales.my.salesforce.com",
    "auth": "services/oauth2/token",
    "client_id": "3MVG97quAmFZJfVzTx173IXur1CB1NY7iqvePR.lXhX43dRkQcqzT1yEgbiQ1k9yNxcs6xszwqsPG11ev.ojO",
    "client_secret": "875DDF9802E6D6E4C124BC7F027F5014D5D78DFCBF5E9FDCB471407685AE484E"
}


class SalesforceService:
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    def __post_init__(self):
        if self.config and not self.config.get("url_domain") and not self.config.get("auth") and not self.config.get("client_id") and not self.config.get("client_secret"):
            self.config = AUTH_FIELDS
    
    def _perform_query(self, access_token, query, format = False):
        url = urljoin(AUTH_FIELDS["url_domain"], f"services/data/v62.0/query")
        headers = {
            'Authorization': f'Bearer {access_token}',
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
    
    def get_opportunity_products(self, access_token, user_ids, account_id, product_ids = [], format = False):   
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
        opportunity_products = self._perform_query(access_token, new_query, format)
        
        return opportunity_products


    def get_opportunities_assigned_to_users(self, access_token, user_ids, account_id, product_ids = [], format = False):
        users_filter = ""
        if user_ids:
            # Add single quotes around each ID and join them with commas
            quoted_ids = [f"'{id}'" for id in user_ids]
            users_filter = f" AND OwnerId IN ({','.join(quoted_ids)})"
        
        opportunity_query = f"SELECT Id, Name, StageName, AccountId, Account.Name, CreatedDate FROM Opportunity WHERE AccountId = '{account_id}'{users_filter} ORDER BY CreatedDate DESC"
        
        opportunities = self._perform_query(access_token, opportunity_query, format)
                
        return opportunities
