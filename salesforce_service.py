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


def authenticate() -> Dict[str, str]:
    """
    Authenticate with Salesforce and return access token with expiration.
    
    Returns:
        Dict containing access_token and expires_in
    
    Raises:
        requests.exceptions.RequestException: If authentication fails
    """
    try:
        # Construct the authentication URL
        url = urljoin(AUTH_FIELDS["url_domain"], AUTH_FIELDS["auth"])
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        # Prepare data
        data = {
            'grant_type': 'client_credentials',
            'client_id': AUTH_FIELDS["client_id"],
            'client_secret': AUTH_FIELDS["client_secret"]
        }
        
        # Make the authentication request
        token_response = requests.post(url, data=data, headers=headers)
        token_response.raise_for_status()  # Raise exception for non-200 status codes
        token_data = token_response.json()
        
        logger.info('Authentication successful')
        logger.debug(f'Token response: {token_data}')
        
        # Introspect the token
        introspect_response = introspect_token(token_data['access_token'])
        
        if not introspect_response.get('active'):
            logger.error('Salesforce token is not active')
            raise requests.exceptions.HTTPError('Salesforce token is not active')
        
        return {
            'access_token': token_data['access_token'],
            'expires_in': introspect_response['exp']
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f'Error authenticating to Salesforce: {str(e)}')
        raise


def introspect_token(access_token: str) -> Dict:
    """
    Introspect the Salesforce token to verify its validity.
    
    Args:
        access_token: The access token to introspect
        
    Returns:
        Dict containing token introspection details
        
    Raises:
        requests.exceptions.RequestException: If introspection fails
    """
    try:
        # Construct the introspection URL (you'll need to replace this with actual endpoint)
        url = urljoin(AUTH_FIELDS["url_domain"], "services/oauth2/introspect")
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
        }
        
        data = {
            'token': access_token,
            'client_id': AUTH_FIELDS["client_id"],
            'client_secret': AUTH_FIELDS["client_secret"],
            'token_type_hint': 'access_token'
        }
        
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f'Error introspecting token: {str(e)}')
        raise


def get_opportunities_assigned_to_user(access_token, user_id, account_id):
    url = urljoin(AUTH_FIELDS["url_domain"], "services/data/v60.0/query")
    
    query = f"SELECT Id, Name, StageName, AccountId, Account.Name, CreatedDate FROM Opportunity WHERE OwnerId = '{user_id}' AND AccountId = '{account_id}' ORDER BY CreatedDate DESC"
   
    logger.debug(f"Query: {query}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(url, headers=headers, params={'q': query})
    response.raise_for_status()
    
    return response.json()
