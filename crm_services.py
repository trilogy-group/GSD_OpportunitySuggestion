import requests
from urllib.parse import urljoin
from typing import Dict
import xml.etree.ElementTree as ET


class ACRMService:
    def __init__(self, config: Dict[str, str]):
        self.config = config

    def _parse_xml_opportunities(self, xml_content: str) -> list:
        """Parse XML response and extract opportunity data"""
        if not xml_content:
            return []
            
        try:
            root = ET.fromstring(xml_content)
            opportunities = []
            
            # Find all Opportunity elements in the XML that have an id attribute
            for opp in root.findall('.//Opportunity[@id]'):
                opportunity_data = {
                    'id': opp.get('id'),  # Get the id attribute
                    'name': opp.find('Opportunity').text if opp.find('Opportunity') is not None else '',
                    'stage': opp.find('Status').text if opp.find('Status') is not None else ''
                }
                opportunities.append(opportunity_data)
            
            return opportunities
            
        except ET.ParseError as e:
            print(f"Failed to parse XML: {str(e)}")
            return []

    def get_opportunity_products(self, user_ids, account_id, product_ids = [], format = False):
        # TODO: Implement the logic to get the products for the opportunities
        return []

    def get_opportunities_by_account_id(self, account_id, format = False):
        query = f"""
        <request pwd="{self.config.get('password')}" user="{self.config.get('username')}">
            <query>
                <tables>
                    <table table="FI" recId="{account_id}">
                        <table table="Y1" />
                    </table>
                </tables>
                <fields table="Y1" fields="6,7,8,15,16,17,43,51" />
            </query>
        </request>
        """
        headers = {
            'Content-Type': 'application/xml',
            'Accept': 'application/xml'
        }

        try:
            response = requests.post(self.config.get("url_domain"), headers=headers, data=query)
            response.raise_for_status()

            opportunities = self._parse_xml_opportunities(response.text)
            
            if format:
                return opportunities
            
            return {
                "totalSize": len(opportunities),
                "records": opportunities
            }

        except Exception as e:
            print(f"Error fetching opportunities by account ID: {e}")
            return [] if format else {"totalSize": 0, "records": []}


class PivotalService:
    def __init__(self, config: Dict[str, str]):
        self.config = config
            
    def _retrieve_form_record(self, access_token, record_id, payload):
        url = urljoin(self.config.get("url_domain"), f"/PivotalUx/rest/forms/formData/actions/retrieve?recordId={record_id}&form={self.config.get('form_name')}")
        
        print(f"URL: {url}")
        
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.config.get("access_token")}',
            'Content-Type': 'application/json',
            'pivotalEnvironmentName': self.config.get('pivotal_environment_name')
        }
        
        print(f"Making request to URL: {url}")
        print(f"Headers: {headers}")
        print(f"Payload: {payload}")
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            
            print(f"Response status code: {response.status_code}")

            # Check if response is successful
            response.raise_for_status()
            
            # Check if response has content
            if not response.text:
                print("Empty response received")
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
            print(f"Request failed: {str(e)}")
            return []
        except ValueError as e:
            print(f"JSON decode failed: {str(e)}")
            return []

    def get_opportunities_by_account_id(self, account_id, format = False):
        print(f"Getting opportunities for account: {account_id}")
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
        
        print(f"Opportunities: {opportunities}")

        return opportunities

    def get_opportunity_products(self, user_ids, account_id, product_ids = [], format = False):
        # TODO: Implement the logic to get the products for the opportunities
        return []


class SalesforceService:

    def __init__(self, config: Dict[str, str]):

        self.config = config
    
    def _perform_query(self, query, format = False):
        url = urljoin(self.config.get("url_domain"), f"services/data/v62.0/query")
        headers = {
            'Authorization': f'Bearer {self.config.get("access_token")}',
            'Content-Type': 'application/json'
        }
        
        print(f"URL: {url}")
        print(f"Query: {query}")
        
        response = requests.get(url, headers=headers, params={'q': query})
        
        if response.status_code != 200:
            print(f"Failed to fetch data: {response.status_code} - {response.text}")
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
            print(f"Error fetching opportunity products: {e}")
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
            print(f"Error fetching opportunities by account ID: {e}")
            return []
