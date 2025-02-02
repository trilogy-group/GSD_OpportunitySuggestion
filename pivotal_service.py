import requests
import logging
from urllib.parse import urljoin
from typing import Dict


# Configure logging
logger = logging.getLogger(__name__)


AUTH_FIELDS = {
    "url_domain": "http://ec2-54-80-60-27.compute-1.amazonaws.com",
    "form_name": "UXCompany",
    "pivotal_environment_name": "Production env"
}


class PivotalService:
    def __init__(self, config: Dict[str, str]):
        self.config = config
    
    def __post_init__(self):
        if self.config and not self.config.get("url_domain"):
            self.config = AUTH_FIELDS
            
    def _retrieve_form_record(self, access_token, record_id, payload):
        url = urljoin(self.config.get("url_domain"), f"/PivotalUx/rest/forms/formData/actions/retrieve?recordId={record_id}&form={self.config.get('form_name')}")
        
        logger.debug(f"URL: {url}")
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.config.get("access_token")}',
            'Content-Type': 'application/json',
            'pivotalEnvironmentName': self.config.get('pivotal_environment_name')
        }
        
        logger.debug(f"Making request to URL: {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Payload: {payload}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            logger.debug(f"Response status code: {response.status_code}")

            # Check if response is successful
            response.raise_for_status()
            
            # Check if response has content
            if not response.text:
                logger.warning("Empty response received")
                return []
                
            json_response = response.json()
            success = json_response['success']
            total_size = 1 if json_response['success'] == True else 0
            records = json_response['payload']['data']['primary'] if success else []
            
            return {
                "success": success,
                "totalSize": total_size,
                "records": [records] if total_size == 1 else records
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return []
        except ValueError as e:
            logger.error(f"JSON decode failed: {str(e)}")
            return []

    def get_opportunities_by_account_id(self, account_id, format = False):
        logger.info(f"Getting opportunities for account: {account_id}")
        result = self._retrieve_form_record(account_id, {})        
        parent_record = result.get('records')[0] if result.get('totalSize') == 1 else None        
        raw_opportunities = parent_record.get('Opportunities__Secondary', []) if parent_record else []
        opportunities = [
            {
                "id": opportunity.get('SFA_Opportunity_Id'),
                "name": opportunity.get('Opportunity_Name'),
                "stage": opportunity.get('Status')
            } for opportunity in raw_opportunities
        ]
        
        logger.debug(f"Opportunities: {opportunities}")

        return opportunities

    def get_opportunity_products(self, user_ids, account_id, product_ids = [], format = False):
        return []


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    config = {
        "url_domain": "http://ec2-54-80-60-27.compute-1.amazonaws.com",
        "form_name": "UXCompany",
        "pivotal_environment_name": "Production env",
        "access_token": "1d35882817f24269b2b41151e5339f84b9cc37638bf4454c9503cb98883301bf56b525d4ccac45e2a583b148fffcd136"
    }
    
    pivotal_svc = PivotalService(config)
    
    try:
        oops = pivotal_svc.get_opportunities_by_account_id(
            "AAAAAAAAAl4="
        )
        print("Result:", oops)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
