"""
Unit tests for Identity Provider API endpoints.
Tests authentication, profile, and basic API functionality.
"""
import json
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework import status

from ..models import Service, Role, UserRole


class BaseAPITestCase(TestCase):
    """Base test case with common setup for API tests."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create test users
        self.test_user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testuser123!#QWERT',
            first_name='Test',
            last_name='User'
        )
        
        self.admin_user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='adminuser123!#QWERT',
            first_name='Admin',
            last_name='User',
            is_staff=True
        )
        
        # Create identity provider service and admin role
        self.identity_service = Service.objects.create(
            name='identity_provider',
            display_name='Identity Provider',
            description='Core identity service',
            is_active=True
        )
        
        self.admin_role = Role.objects.create(
            service=self.identity_service,
            name='identity_admin',
            display_name='Identity Administrator',
            description='Full admin access',
            is_global=True
        )
        
        # Assign admin role to admin user
        UserRole.objects.create(
            user=self.admin_user,
            role=self.admin_role,
            granted_by=self.admin_user
        )


class LoginAPITestCase(BaseAPITestCase):
    """Test cases for login API endpoint."""
    
    def test_login_success(self):
        """Test successful login via API."""
        url = reverse('api_login')
        data = {
            'username': 'testuser',
            'password': 'testuser123!#QWERT'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertIn('token', response_data)
        self.assertIsInstance(response_data['token'], str)
        self.assertTrue(len(response_data['token']) > 0)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('api_login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Invalid credentials')
    
    def test_login_missing_username(self):
        """Test login with missing username."""
        url = reverse('api_login')
        data = {
            'password': 'testuser123!#QWERT'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Username and password are required')
    
    def test_login_missing_password(self):
        """Test login with missing password."""
        url = reverse('api_login')
        data = {
            'username': 'testuser'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Username and password are required')
    
    def test_login_invalid_json(self):
        """Test login with invalid JSON."""
        url = reverse('api_login')
        
        response = self.client.post(
            url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)


class WebLoginTestCase(BaseAPITestCase):
    """Test cases for web-based login."""
    
    def test_login_page_get(self):
        """Test GET request to login page."""
        url = reverse('login')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTemplateUsed(response, 'identity_app/login.html')
    
    def test_login_page_with_redirect_uri(self):
        """Test login page with redirect_uri parameter."""
        url = reverse('login')
        response = self.client.get(url, {'redirect_uri': 'https://example.com'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @patch('identity_app.views.utils.encode_jwt')
    def test_web_login_success(self, mock_encode_jwt):
        """Test successful web login."""
        mock_encode_jwt.return_value = 'test_jwt_token'
        
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testuser123!#QWERT'
        }
        
        response = self.client.post(url, data)
        
        # Should redirect after successful login
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        # Check JWT cookie is set
        self.assertIn('jwt', response.cookies)
        self.assertEqual(response.cookies['jwt'].value, 'test_jwt_token')
    
    def test_web_login_invalid_credentials(self):
        """Test web login with invalid credentials."""
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(b'Invalid login', response.content)


class LogoutTestCase(BaseAPITestCase):
    """Test cases for logout functionality."""
    
    def test_logout_clears_cookie(self):
        """Test that logout clears JWT cookie."""
        url = reverse('logout')
        
        # Set a cookie first
        self.client.cookies['jwt'] = 'test_token'
        
        response = self.client.get(url)
        
        # Should redirect
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        # Cookie should be deleted
        self.assertEqual(response.cookies['jwt'].value, '')
        self.assertEqual(response.cookies['jwt']['max-age'], 0)


class APIInfoTestCase(BaseAPITestCase):
    """Test cases for API info endpoints."""
    
    def test_api_info(self):
        """Test API info endpoint."""
        url = reverse('api_info')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertIn('service', response_data)
        self.assertIn('version', response_data)
        self.assertIn('endpoints', response_data)
        self.assertIn('timestamp', response_data)
        self.assertEqual(response_data['service'], 'Identity Provider API')
    
    def test_api_status(self):
        """Test API status endpoint."""
        url = reverse('api_status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['status'], 'healthy')
        self.assertEqual(response_data['service'], 'identity-provider')
        self.assertIn('timestamp', response_data)


class ProfileAPITestCase(BaseAPITestCase):
    """Test cases for profile API endpoint."""
    
    def test_profile_authenticated(self):
        """Test profile endpoint with authenticated user."""
        # Skip this test as it requires JWT middleware setup
        self.skipTest("Requires JWT middleware setup")
        
        # Force login as admin user
        self.client.force_login(self.admin_user)
        
        url = reverse('api_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['id'], self.admin_user.id)
        self.assertEqual(response_data['username'], 'adminuser')
        self.assertEqual(response_data['email'], 'admin@example.com')
        self.assertIn('roles', response_data)
        self.assertEqual(len(response_data['roles']), 1)
        self.assertEqual(response_data['roles'][0]['role_name'], 'identity_admin')
    
    def test_profile_unauthenticated(self):
        """Test profile endpoint without authentication."""
        url = reverse('api_profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ServiceRegistrationTestCase(BaseAPITestCase):
    """Test cases for service registration endpoint."""
    
    def test_register_service_success(self):
        """Test successful service registration."""
        url = reverse('service_register')
        data = {
            'service': 'test_service',
            'display_name': 'Test Service',
            'description': 'A test service',
            'manifest_version': '1.0',
            'roles': [
                {
                    'name': 'test_admin',
                    'display_name': 'Test Administrator',
                    'description': 'Admin role for test service',
                    'is_global': True
                },
                {
                    'name': 'test_viewer',
                    'display_name': 'Test Viewer',
                    'description': 'Viewer role for test service',
                    'is_global': False
                }
            ],
            'attributes': [
                {
                    'name': 'department',
                    'display_name': 'Department',
                    'description': 'User department',
                    'type': 'string',
                    'is_required': False
                }
            ]
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['service'], 'test_service')
        self.assertIn('version', response_data)  # Check for version instead of status
        self.assertIn('registered_at', response_data)
        self.assertTrue(response_data['is_active'])
    
    def test_register_service_missing_fields(self):
        """Test service registration with missing required fields."""
        url = reverse('service_register')
        data = {
            'service': 'test_service'
            # Missing required fields
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertIn('missing_fields', response_data)
    
    def test_register_service_invalid_name_format(self):
        """Test service registration with invalid service name format."""
        url = reverse('service_register')
        data = {
            'service': 'Invalid-Service-Name',  # Should be lowercase with underscores
            'display_name': 'Test Service',
            'roles': [],
            'attributes': []
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertIn('Invalid service name format', response_data['detail'])


class RefreshCacheTestCase(BaseAPITestCase):
    """Test cases for cache refresh endpoint."""
    
    @patch('identity_app.services.RedisService.populate_user_attributes')
    def test_refresh_cache_success(self, mock_populate):
        """Test successful cache refresh."""
        mock_populate.return_value = True
        
        url = reverse('refresh_user_cache')
        data = {
            'user_id': self.test_user.id,
            'service_name': 'test_service'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        self.assertEqual(response_data['detail'], 'Cache refreshed successfully')
        
        # Verify the service was called
        mock_populate.assert_called_once_with(self.test_user.id, 'test_service')
    
    @patch('identity_app.services.RedisService.populate_user_attributes')
    def test_refresh_cache_user_not_found(self, mock_populate):
        """Test cache refresh when user not found."""
        mock_populate.return_value = False
        
        url = reverse('refresh_user_cache')
        data = {
            'user_id': 99999,
            'service_name': 'test_service'
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response_data = response.json()
        self.assertEqual(response_data['detail'], 'User or service not found')
    
    def test_refresh_cache_missing_parameters(self):
        """Test cache refresh with missing parameters."""
        url = reverse('refresh_user_cache')
        data = {
            'user_id': self.test_user.id
            # Missing service_name
        }
        
        response = self.client.post(
            url,
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertEqual(response_data['detail'], 'Both user_id and service_name are required')


class IndexViewTestCase(BaseAPITestCase):
    """Test cases for index view."""
    
    def test_index_redirects_to_login(self):
        """Test that root URL redirects to login."""
        url = '/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response.url, '/login/')