"""
API Client for Identity Provider Admin endpoints
"""
import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from django.conf import settings

from .exceptions import (
    APIError, AuthenticationError, PermissionError, 
    ValidationError, NotFoundError, NetworkError, TimeoutError
)
from .constants import ROLE_PROFILES, DEFAULT_API_TIMEOUT

logger = logging.getLogger(__name__)


class IdentityAdminAPIClient:
    """
    Client for Identity Provider Admin API.
    
    No caching as per requirements - always fetches fresh data.
    """
    
    def __init__(self, jwt_token: str, base_url: str = None, timeout: int = None):
        """
        Initialize API client.
        
        Args:
            jwt_token: JWT authentication token
            base_url: Base URL for Identity Provider API
            timeout: Request timeout in seconds
        """
        self.token = jwt_token
        self.base_url = base_url or getattr(
            settings, 
            'IDENTITY_PROVIDER_URL', 
            'https://identity.vfservices.viloforge.com'
        )
        self.timeout = timeout or getattr(
            settings,
            'IDENTITY_ADMIN_API_TIMEOUT',
            DEFAULT_API_TIMEOUT
        )
        
        # Create session with default headers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })
        
        # Disable SSL warnings for development
        if settings.DEBUG:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make HTTP request to API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests
            
        Returns:
            Response data as dictionary
            
        Raises:
            Various APIError subclasses based on response
        """
        url = urljoin(self.base_url, endpoint)
        
        # Set default timeout
        kwargs.setdefault('timeout', self.timeout)
        
        # Disable SSL verification in development
        if settings.DEBUG:
            kwargs.setdefault('verify', False)
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle different status codes
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed - token may be expired",
                    status_code=401,
                    response=response
                )
            elif response.status_code == 403:
                raise PermissionError(
                    "Permission denied - insufficient privileges",
                    status_code=403,
                    response=response
                )
            elif response.status_code == 404:
                raise NotFoundError(
                    "Resource not found",
                    status_code=404,
                    response=response
                )
            elif response.status_code >= 400:
                # Try to get error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', str(error_data))
                except:
                    error_msg = response.text or f"HTTP {response.status_code}"
                
                if response.status_code < 500:
                    raise ValidationError(error_msg, status_code=response.status_code, response=response)
                else:
                    raise APIError(f"Server error: {error_msg}", status_code=response.status_code, response=response)
            
            # Success - return JSON data
            return response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")
    
    # User Management Methods
    
    def list_users(self, page: int = 1, page_size: int = 50, 
                   search: str = None, **filters) -> Dict[str, Any]:
        """
        List users with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            page_size: Number of results per page
            search: Search term for username, email, name
            **filters: Additional filters (is_active, has_role, service)
            
        Returns:
            Dictionary with 'count', 'results', 'next', 'previous'
        """
        params = {
            'page': page,
            'page_size': page_size,
        }
        
        if search:
            params['search'] = search
            
        # Add any additional filters
        params.update(filters)
        
        return self._request('GET', '/api/admin/users/', params=params)
    
    def get_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get user details including roles.
        
        Args:
            user_id: User ID
            
        Returns:
            User data with roles
        """
        return self._request('GET', f'/api/admin/users/{user_id}/')
    
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user with optional initial roles.
        
        Args:
            user_data: Dictionary with user fields
                - username (required)
                - email (required)
                - password (required)
                - first_name (optional)
                - last_name (optional)
                - initial_roles (optional): List of role assignments
                
        Returns:
            Created user data
        """
        return self._request('POST', '/api/admin/users/', json=user_data)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user information.
        
        Args:
            user_id: User ID
            user_data: Fields to update
            
        Returns:
            Updated user data
        """
        return self._request('PUT', f'/api/admin/users/{user_id}/', json=user_data)
    
    def deactivate_user(self, user_id: int) -> Dict[str, Any]:
        """
        Soft delete user.
        
        Args:
            user_id: User ID
            
        Returns:
            Success message
        """
        return self._request('DELETE', f'/api/admin/users/{user_id}/')
    
    def set_user_password(self, user_id: int, password: str) -> Dict[str, Any]:
        """
        Set user password.
        
        Args:
            user_id: User ID
            password: New password
            
        Returns:
            Success message
        """
        return self._request('POST', f'/api/admin/users/{user_id}/set-password/', 
                           json={'password': password})
    
    # Role Management Methods
    
    def list_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get user's current roles.
        
        Args:
            user_id: User ID
            
        Returns:
            List of role assignments
        """
        return self._request('GET', f'/api/admin/users/{user_id}/roles/')
    
    def assign_role(self, user_id: int, role_name: str, service_name: str,
                   expires_at: str = None, reason: str = None) -> Dict[str, Any]:
        """
        Assign role to user.
        
        Args:
            user_id: User ID
            role_name: Name of the role
            service_name: Name of the service
            expires_at: Optional expiration date (ISO format)
            reason: Optional reason for assignment
            
        Returns:
            Created role assignment
        """
        data = {
            'role_name': role_name,
            'service_name': service_name,
        }
        
        if expires_at:
            data['expires_at'] = expires_at
        if reason:
            data['reason'] = reason
            
        return self._request('POST', f'/api/admin/users/{user_id}/roles/', json=data)
    
    def revoke_role(self, user_id: int, role_id: int, reason: str = None) -> Dict[str, Any]:
        """
        Revoke role from user.
        
        Args:
            user_id: User ID
            role_id: Role assignment ID
            reason: Optional reason for revocation
            
        Returns:
            Success message
        """
        data = {}
        if reason:
            data['reason'] = reason
            
        return self._request('DELETE', f'/api/admin/users/{user_id}/roles/{role_id}/', 
                           json=data if data else None)
    
    def assign_role_profile(self, user_id: int, profile_key: str,
                          expires_at: str = None, reason: str = None) -> List[Dict[str, Any]]:
        """
        Assign a role profile (set of roles) to user.
        
        Args:
            user_id: User ID
            profile_key: Key from ROLE_PROFILES
            expires_at: Optional expiration date for all roles
            reason: Optional reason for assignment
            
        Returns:
            List of results for each role assignment
        """
        profile = ROLE_PROFILES.get(profile_key)
        if not profile:
            raise ValueError(f"Unknown role profile: {profile_key}")
        
        results = []
        for role_name, service_name in profile['roles']:
            try:
                result = self.assign_role(
                    user_id, role_name, service_name, expires_at, 
                    reason or f"Assigned via {profile['name']} profile"
                )
                results.append({
                    'success': True, 
                    'role': role_name, 
                    'service': service_name,
                    'data': result
                })
            except Exception as e:
                results.append({
                    'success': False, 
                    'role': role_name, 
                    'service': service_name, 
                    'error': str(e)
                })
        
        return results
    
    # Service and Role Methods
    
    def list_services(self) -> List[Dict[str, Any]]:
        """
        List all registered services.
        
        Returns:
            List of services
        """
        return self._request('GET', '/api/admin/services/')
    
    def list_roles(self, service: str = None, is_global: bool = None) -> List[Dict[str, Any]]:
        """
        List all available roles.
        
        Args:
            service: Filter by service name
            is_global: Filter by global status
            
        Returns:
            List of roles
        """
        params = {}
        if service is not None:
            params['service'] = service
        if is_global is not None:
            params['is_global'] = str(is_global).lower()
            
        return self._request('GET', '/api/admin/roles/', params=params)
    
    # User Attributes Methods
    
    def get_user_attributes(self, user_id: int) -> Dict[str, Any]:
        """
        Get user attributes.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary of attributes
        """
        # This would typically be part of the user detail response
        # but we'll implement it as a separate endpoint for flexibility
        user_data = self.get_user(user_id)
        return user_data.get('attributes', {})