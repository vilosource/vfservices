"""
Smoke tests for newly implemented API endpoints:
- API Logout
- User Attributes Management
- Service Attributes Management
"""
import os
import time
import requests
import pytest
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

BASE_URL = os.environ.get('IDENTITY_PROVIDER_URL', 'https://identity.vfservices.viloforge.com')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')


def get_admin_token():
    """Get admin JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/login/", 
        json={
            'username': ADMIN_USERNAME,
            'password': ADMIN_PASSWORD
        },
        verify=False
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to login: {response.text}")
    
    return response.json()['token']


def get_test_user_id():
    """Get a test user ID"""
    token = get_admin_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(
        f"{BASE_URL}/api/admin/users/",
        headers=headers,
        verify=False
    )
    
    if response.status_code != 200:
        raise Exception(f"Failed to get users: {response.text}")
    
    users = response.json()['results']
    # Find a non-admin user
    for user in users:
        if user['username'] != ADMIN_USERNAME:
            return user['id']
    
    # If no other user found, use the first one
    return users[0]['id'] if users else None


def get_billing_service_id():
    """Get billing service ID if it exists"""
    token = get_admin_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(
        f"{BASE_URL}/api/admin/services/",
        headers=headers,
        verify=False
    )
    
    if response.status_code == 200:
        services = response.json()
        for service in services:
            if service['name'] == 'billing_api':
                return service['id']
    
    return None


class TestAPILogout:
    """Test API Logout endpoint"""
    
    def test_logout_with_bearer_token(self):
        """Test logout with JWT bearer token"""
        # Get a fresh token
        token = get_admin_token()
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/logout/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        assert response.json()['detail'] == 'Logged out successfully'
        print("✓ API logout successful")
    
    def test_logout_without_token(self):
        """Test logout without authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/logout/",
            verify=False
        )
        
        assert response.status_code == 400
        assert 'No authentication token provided' in response.json()['detail']
        print("✓ Logout without token rejected")
    
    def test_logout_with_invalid_token(self):
        """Test logout with invalid token"""
        headers = {
            'Authorization': 'Bearer invalid_token_12345'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/logout/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 401
        assert 'Invalid authentication token' in response.json()['detail']
        print("✓ Logout with invalid token rejected")


class TestUserAttributesAPI:
    """Test User Attributes Management API"""
    
    def test_list_user_attributes(self):
        """Test listing user attributes"""
        token = get_admin_token()
        user_id = get_test_user_id()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/users/{user_id}/attributes/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print(f"✓ Listed attributes for user {user_id}")
    
    def test_create_user_attribute(self):
        """Test creating a user attribute"""
        token = get_admin_token()
        user_id = get_test_user_id()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        attribute_data = {
            'name': f'test_location_{int(time.time())}',
            'value': 'New York'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/set_attribute/",
            json=attribute_data,
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == attribute_data['name']
        assert data['value'] == attribute_data['value']
        print(f"✓ Created attribute {attribute_data['name']} for user {user_id}")
        
        return attribute_data['name']
    
    def test_update_user_attribute(self):
        """Test updating an existing attribute"""
        token = get_admin_token()
        user_id = get_test_user_id()
        
        # First create an attribute
        attr_name = self.test_create_user_attribute()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        # Update it
        update_data = {
            'name': attr_name,
            'value': 'San Francisco'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/set_attribute/",
            json=update_data,
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['value'] == 'San Francisco'
        print(f"✓ Updated attribute {attr_name}")
    
    def test_delete_user_attribute(self):
        """Test deleting a user attribute"""
        token = get_admin_token()
        user_id = get_test_user_id()
        
        # First create an attribute
        attr_name = self.test_create_user_attribute()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/users/{user_id}/attributes/{attr_name}/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 204
        print(f"✓ Deleted attribute {attr_name}")
    
    def test_invalid_attribute_name(self):
        """Test creating attribute with invalid name"""
        token = get_admin_token()
        user_id = get_test_user_id()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        attribute_data = {
            'name': 'Invalid-Name',  # Contains uppercase and hyphen
            'value': 'test'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/users/{user_id}/set_attribute/",
            json=attribute_data,
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 400
        assert 'name' in response.json()
        print("✓ Invalid attribute name rejected")


class TestServiceAttributesAPI:
    """Test Service Attributes Management API"""
    
    def test_list_service_attributes(self):
        """Test listing service attributes"""
        token = get_admin_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/attributes/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✓ Listed service attributes")
    
    def test_create_service_attribute(self):
        """Test creating a service attribute definition"""
        token = get_admin_token()
        service_id = get_billing_service_id()
        
        if not service_id:
            pytest.skip("Billing service not found")
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        attribute_data = {
            'service_id': service_id,
            'name': f'test_access_level_{int(time.time())}',
            'display_name': 'Test Access Level',
            'description': 'User access level for testing',
            'attribute_type': 'string',
            'is_required': False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/attributes/",
            json=attribute_data,
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == attribute_data['name']
        assert data['attribute_type'] == 'string'
        print(f"✓ Created service attribute {attribute_data['name']}")
        
        return data['id']
    
    def test_update_service_attribute(self):
        """Test updating a service attribute"""
        token = get_admin_token()
        attr_id = self.test_create_service_attribute()
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        }
        
        update_data = {
            'display_name': 'Updated Test Access Level',
            'is_required': True
        }
        
        response = requests.patch(
            f"{BASE_URL}/api/admin/attributes/{attr_id}/",
            json=update_data,
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['display_name'] == 'Updated Test Access Level'
        assert data['is_required'] is True
        print(f"✓ Updated service attribute {attr_id}")
    
    def test_delete_service_attribute(self):
        """Test deleting a service attribute"""
        token = get_admin_token()
        attr_id = self.test_create_service_attribute()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/attributes/{attr_id}/",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 204
        print(f"✓ Deleted service attribute {attr_id}")
    
    def test_filter_attributes_by_service(self):
        """Test filtering attributes by service"""
        token = get_admin_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        response = requests.get(
            f"{BASE_URL}/api/admin/attributes/?service=billing_api",
            headers=headers,
            verify=False
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check all returned attributes belong to billing_api
        for attr in data:
            if 'service_name' in attr:
                assert attr['service_name'] == 'billing_api'
        
        print("✓ Filtered attributes by service")


class TestPermissions:
    """Test permission requirements"""
    
    def test_unauthenticated_access(self):
        """Test that endpoints require authentication"""
        user_id = 1  # Any ID
        
        # Test user attributes endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/users/{user_id}/attributes/",
            verify=False
        )
        assert response.status_code == 403
        
        # Test service attributes endpoint
        response = requests.get(
            f"{BASE_URL}/api/admin/attributes/",
            verify=False
        )
        assert response.status_code == 403
        
        print("✓ Unauthenticated requests rejected")


if __name__ == "__main__":
    print(f"Testing Identity Provider at: {BASE_URL}")
    print("=" * 60)
    
    # Run tests
    test_classes = [
        TestAPILogout(),
        TestUserAttributesAPI(),
        TestServiceAttributesAPI(),
        TestPermissions()
    ]
    
    for test_class in test_classes:
        print(f"\n{test_class.__class__.__name__}:")
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                method = getattr(test_class, method_name)
                try:
                    method()
                except Exception as e:
                    print(f"✗ {method_name}: {str(e)}")