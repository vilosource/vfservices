import requests
import logging
from django.conf import settings
from webapp.logging_utils import get_client_ip

logger = logging.getLogger(__name__)

class IdentityProviderClient:
    """Client for communicating with the identity provider service."""
    
    def __init__(self):
        self.base_url = settings.IDENTITY_PROVIDER_URL
        self.timeout = 10
        
    def authenticate_user(self, username, password, request=None):
        """
        Authenticate user via identity provider API.
        
        Args:
            username (str): User's email/username
            password (str): User's password
            request (HttpRequest, optional): For logging purposes
            
        Returns:
            dict: Authentication result with token or error
        """
        client_ip = get_client_ip(request) if request else 'Unknown'
        
        try:
            logger.info(
                f"Attempting authentication for user: {username}",
                extra={
                    'username': username,
                    'client_ip': client_ip,
                    'service': 'identity-provider'
                }
            )
            
            response = requests.post(
                f"{self.base_url}/api/login/",
                json={"username": username, "password": password},
                timeout=self.timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'VF-Website/1.0'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Authentication successful for user: {username}",
                    extra={
                        'username': username,
                        'client_ip': client_ip,
                        'service': 'identity-provider'
                    }
                )
                return result
            else:
                error_detail = response.json().get("detail", "Authentication failed")
                logger.warning(
                    f"Authentication failed for user: {username} - {error_detail}",
                    extra={
                        'username': username,
                        'client_ip': client_ip,
                        'status_code': response.status_code,
                        'error': error_detail
                    }
                )
                return {"error": error_detail}
                
        except requests.Timeout:
            logger.error(
                f"Identity provider timeout for user: {username}",
                extra={'username': username, 'client_ip': client_ip}
            )
            return {"error": "Authentication service timeout"}
            
        except requests.ConnectionError:
            logger.error(
                f"Identity provider connection error for user: {username}",
                extra={'username': username, 'client_ip': client_ip}
            )
            return {"error": "Authentication service unavailable"}
            
        except requests.RequestException as e:
            logger.error(
                f"Identity provider request failed for user: {username} - {str(e)}",
                extra={'username': username, 'client_ip': client_ip, 'error': str(e)}
            )
            return {"error": "Authentication service error"}
        
        except Exception as e:
            logger.error(
                f"Unexpected error during authentication for user: {username} - {str(e)}",
                extra={'username': username, 'client_ip': client_ip, 'error': str(e)},
                exc_info=True
            )
            return {"error": "Authentication system error"}