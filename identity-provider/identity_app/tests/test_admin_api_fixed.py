"""
Fixed tests for Identity Provider Admin API endpoints.
Properly handles JWT authentication in test environment.
"""
import json
from datetime import timedelta
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from ..models import Service, Role, UserRole, ServiceManifest
from ..services import RedisService

# Import JWT utilities from common module
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.jwt_auth import utils as jwt_utils


class JWTAuthMixin:
    """Mixin to handle JWT authentication in tests."""
    
    def authenticate_with_jwt(self, user):
        """Create and set JWT token for the given user."""
        # Create JWT payload
        payload = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "iat": timezone.now(),
        }
        
        # Generate JWT token
        token = jwt_utils.encode_jwt(payload)
        
        # Set the JWT cookie
        self.client.cookies['jwt'] = token
        
        # Also set it in the Authorization header as backup
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        
        return token
    
    def clear_authentication(self):
        """Clear JWT authentication."""
        self.client.cookies.clear()
        self.client.credentials()


@override_settings(
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'common.jwt_auth.middleware.JWTAuthMiddleware',  # Ensure JWT middleware is active
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
)
class AdminAPITestCase(TestCase, JWTAuthMixin):
    """Base test case for admin API with proper JWT authentication."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create identity provider service
        self.identity_service = Service.objects.create(
            name='identity_provider',
            display_name='Identity Provider',
            description='Core identity service',
            is_active=True
        )
        
        # Create identity_admin role
        self.admin_role = Role.objects.create(
            name='identity_admin',
            display_name='Identity Administrator',
            service=self.identity_service,
            is_global=True,
            description='Full admin access'
        )
        
        # Create admin user with identity_admin role
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123!#QWERT',
            first_name='Admin',
            last_name='User'
        )
        
        UserRole.objects.create(
            user=self.admin_user,
            role=self.admin_role,
            granted_by=self.admin_user
        )
        
        # Create regular test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testuser123!#QWERT',
            first_name='Test',
            last_name='User'
        )
        
        # Create additional test service
        self.billing_service = Service.objects.create(
            name='billing_api',
            display_name='Billing API',
            description='Billing service',
            is_active=True
        )
        
        self.billing_admin_role = Role.objects.create(
            name='billing_admin',
            display_name='Billing Administrator',
            service=self.billing_service,
            is_global=True
        )
        
        # Authenticate as admin by default
        self.authenticate_with_jwt(self.admin_user)


class UserAPITestCase(AdminAPITestCase):
    """Test cases for user management endpoints with proper JWT auth."""
    
    def test_list_users_authenticated(self):
        """Test listing users with JWT authentication."""
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)  # admin and test user
    
    def test_create_user_authenticated(self):
        """Test creating user with JWT authentication."""
        url = reverse('admin-user-list')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newuser123!#QWERT',
            'first_name': 'New',
            'last_name': 'User',
            'is_active': True,
            'initial_roles': [
                {
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['username'], 'newuser')
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('newuser123!#QWERT'))
    
    def test_update_user_authenticated(self):
        """Test updating user with JWT authentication."""
        url = reverse('admin-user-detail', kwargs={'pk': self.test_user.id})
        data = {
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.email, 'updated@example.com')
    
    def test_unauthorized_without_jwt(self):
        """Test that requests without JWT are rejected."""
        # Clear authentication
        self.clear_authentication()
        
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_non_admin_user_forbidden(self):
        """Test that non-admin users are forbidden."""
        # Authenticate as regular user
        self.authenticate_with_jwt(self.test_user)
        
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    def test_role_assignment_with_cache_invalidation(self, mock_invalidate):
        """Test role assignment invalidates cache."""
        url = reverse('admin-user-roles', kwargs={'pk': self.test_user.id})
        data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api',
            'reason': 'Test assignment'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify cache was invalidated
        mock_invalidate.assert_called_with(self.test_user.id)
        
        # Verify role was assigned
        self.assertTrue(
            UserRole.objects.filter(
                user=self.test_user,
                role__name='billing_admin'
            ).exists()
        )


class ServiceAPITestCase(AdminAPITestCase):
    """Test cases for service endpoints with JWT auth."""
    
    def test_list_services(self):
        """Test listing services."""
        url = reverse('admin-service-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 2)  # identity_provider and billing_api
        
        # Check service data
        service_names = [s['name'] for s in data]
        self.assertIn('identity_provider', service_names)
        self.assertIn('billing_api', service_names)


class BulkOperationsTestCase(AdminAPITestCase):
    """Test cases for bulk operations with JWT auth."""
    
    def test_bulk_assign_roles(self):
        """Test bulk role assignment."""
        # Create additional user
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='user2123!#QWERT'
        )
        
        url = reverse('admin-bulk-assign-roles')
        data = {
            'assignments': [
                {
                    'username': 'testuser',
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                },
                {
                    'username': 'user2',
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ],
            'reason': 'Bulk test assignment'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['total'], 2)
        self.assertEqual(response_data['success'], 2)
        self.assertEqual(len(response_data['created']), 2)


# Alternative approach using a custom test middleware
class JWTTestMiddleware:
    """Test middleware that sets user from JWT cookie for tests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check for JWT in cookies
        jwt_token = request.COOKIES.get('jwt')
        if jwt_token:
            try:
                payload = jwt_utils.decode_jwt(jwt_token)
                user_id = payload.get('user_id')
                if user_id:
                    request.user = User.objects.get(id=user_id)
                    request.user.is_authenticated = True
            except Exception:
                pass
        
        response = self.get_response(request)
        return response


# Example of using custom test settings
TEST_MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'identity_app.tests.test_admin_api_fixed.JWTTestMiddleware',  # Custom test middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]