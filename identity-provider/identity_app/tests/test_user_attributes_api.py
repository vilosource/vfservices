"""
Tests for User Attributes API endpoints
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from ..models import Service, Role, UserRole, UserAttribute
from ..services import RedisService


class UserAttributesAPITestCase(TestCase):
    """Test cases for user attributes API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Get or create identity provider service
        self.identity_service, _ = Service.objects.get_or_create(
            name='identity_provider',
            defaults={
                'display_name': 'Identity Provider',
                'description': 'Core identity service',
                'is_active': True
            }
        )
        
        # Get or create identity_admin role
        self.admin_role, _ = Role.objects.get_or_create(
            name='identity_admin',
            service=self.identity_service,
            defaults={
                'display_name': 'Identity Administrator',
                'is_global': True,
                'description': 'Full admin access'
            }
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
        
        # Create another service for testing
        self.billing_service = Service.objects.create(
            name='billing_api',
            display_name='Billing API',
            description='Billing service',
            is_active=True
        )
        
        # Set up JWT authentication mocking
        self.jwt_auth_patcher = patch('identity_app.admin_views.JWTCookieAuthentication.authenticate')
        self.mock_jwt_auth = self.jwt_auth_patcher.start()
        
        # Authenticate as admin by default
        self.mock_jwt_auth.return_value = (self.admin_user, None)
    
    def tearDown(self):
        """Clean up after tests."""
        self.jwt_auth_patcher.stop()
        super().tearDown()
    
    def test_list_user_attributes_empty(self):
        """Test listing attributes when user has none."""
        url = reverse('admin-user-attributes', kwargs={'pk': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data, [])
    
    def test_list_user_attributes_with_data(self):
        """Test listing user attributes."""
        # Create some attributes
        attr1 = UserAttribute.objects.create(
            user=self.test_user,
            name='department',
            value='Engineering',
            updated_by=self.admin_user
        )
        
        attr2 = UserAttribute.objects.create(
            user=self.test_user,
            service=self.billing_service,
            name='billing_tier',
            value='premium',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-user-attributes', kwargs={'pk': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 2)
        
        # Check global attribute
        global_attr = next(a for a in data if a['name'] == 'department')
        self.assertEqual(global_attr['value'], 'Engineering')
        self.assertIsNone(global_attr['service'])
        self.assertIsNone(global_attr['service_name'])
        
        # Check service-specific attribute
        service_attr = next(a for a in data if a['name'] == 'billing_tier')
        self.assertEqual(service_attr['value'], 'premium')
        self.assertEqual(service_attr['service'], self.billing_service.id)
        self.assertEqual(service_attr['service_name'], 'billing_api')
    
    def test_create_user_attribute(self):
        """Test creating a new user attribute."""
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'location',
            'value': 'New York'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['name'], 'location')
        self.assertEqual(response_data['value'], 'New York')
        self.assertIsNone(response_data['service'])
        self.assertEqual(response_data['updated_by_username'], 'admin')
        
        # Verify attribute was created
        attr = UserAttribute.objects.get(user=self.test_user, name='location')
        self.assertEqual(attr.value, 'New York')
    
    def test_update_existing_attribute(self):
        """Test updating an existing attribute."""
        # Create initial attribute
        attr = UserAttribute.objects.create(
            user=self.test_user,
            name='department',
            value='Sales',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'department',
            'value': 'Engineering'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['name'], 'department')
        self.assertEqual(response_data['value'], 'Engineering')
        
        # Verify attribute was updated
        attr.refresh_from_db()
        self.assertEqual(attr.value, 'Engineering')
    
    def test_create_service_specific_attribute(self):
        """Test creating a service-specific attribute."""
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'access_level',
            'value': 'read_only',
            'service_id': self.billing_service.id
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['name'], 'access_level')
        self.assertEqual(response_data['value'], 'read_only')
        self.assertEqual(response_data['service'], self.billing_service.id)
        self.assertEqual(response_data['service_name'], 'billing_api')
    
    def test_create_attribute_with_json_value(self):
        """Test creating an attribute with JSON value."""
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'preferences',
            'value': '{"theme": "dark", "notifications": true}'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['name'], 'preferences')
        self.assertEqual(response_data['value'], '{"theme": "dark", "notifications": true}')
    
    def test_create_attribute_invalid_name(self):
        """Test creating attribute with invalid name format."""
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'Invalid-Name',  # Contains uppercase and hyphen
            'value': 'test'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.json())
    
    def test_create_attribute_invalid_service(self):
        """Test creating attribute with invalid service ID."""
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {
            'name': 'test_attr',
            'value': 'test',
            'service_id': 99999
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('service_id', response.json())
    
    def test_delete_user_attribute(self):
        """Test deleting a user attribute."""
        # Create attribute
        attr = UserAttribute.objects.create(
            user=self.test_user,
            name='department',
            value='Sales',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-user-delete-attribute', kwargs={
            'pk': self.test_user.id,
            'attribute_name': 'department'
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify attribute was deleted
        self.assertFalse(
            UserAttribute.objects.filter(
                user=self.test_user,
                name='department'
            ).exists()
        )
    
    def test_delete_service_specific_attribute(self):
        """Test deleting a service-specific attribute."""
        # Create service-specific attribute
        attr = UserAttribute.objects.create(
            user=self.test_user,
            service=self.billing_service,
            name='access_level',
            value='admin',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-user-delete-attribute', kwargs={
            'pk': self.test_user.id,
            'attribute_name': 'access_level'
        })
        
        # Must specify service_id for service-specific attributes
        response = self.client.delete(f"{url}?service_id={self.billing_service.id}")
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify attribute was deleted
        self.assertFalse(
            UserAttribute.objects.filter(
                user=self.test_user,
                service=self.billing_service,
                name='access_level'
            ).exists()
        )
    
    def test_delete_nonexistent_attribute(self):
        """Test deleting an attribute that doesn't exist."""
        url = reverse('admin-user-delete-attribute', kwargs={
            'pk': self.test_user.id,
            'attribute_name': 'nonexistent'
        })
        
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.json())
    
    def test_requires_admin_permission(self):
        """Test that attribute endpoints require admin permission."""
        # Authenticate as non-admin user
        self.mock_jwt_auth.return_value = (self.test_user, None)
        
        # Mock RBACService to return no admin role
        with patch('identity_app.permissions.RBACService.get_user_roles') as mock_get_roles:
            mock_get_roles.return_value = []
            
            # Test list attributes
            url = reverse('admin-user-attributes', kwargs={'pk': self.test_user.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
            # Test create attribute
            url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
            response = self.client.post(url, {'name': 'test', 'value': 'test'})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
            # Test delete attribute
            url = reverse('admin-user-delete-attribute', kwargs={
                'pk': self.test_user.id,
                'attribute_name': 'test'
            })
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    def test_cache_invalidation_on_attribute_changes(self, mock_invalidate):
        """Test that cache is invalidated when attributes change."""
        # Create attribute
        url = reverse('admin-user-set-attribute', kwargs={'pk': self.test_user.id})
        data = {'name': 'test_attr', 'value': 'test_value'}
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify cache was invalidated
        mock_invalidate.assert_called_with(self.test_user.id)
        
        # Update attribute
        mock_invalidate.reset_mock()
        data['value'] = 'new_value'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache was invalidated again
        mock_invalidate.assert_called_with(self.test_user.id)
        
        # Delete attribute
        mock_invalidate.reset_mock()
        url = reverse('admin-user-delete-attribute', kwargs={
            'pk': self.test_user.id,
            'attribute_name': 'test_attr'
        })
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify cache was invalidated on delete
        mock_invalidate.assert_called_with(self.test_user.id)
    
    def test_attribute_ordering(self):
        """Test that attributes are ordered by service name then attribute name."""
        # Create attributes in random order
        UserAttribute.objects.create(
            user=self.test_user,
            name='z_attr',
            value='1',
            updated_by=self.admin_user
        )
        
        UserAttribute.objects.create(
            user=self.test_user,
            service=self.billing_service,
            name='a_attr',
            value='2',
            updated_by=self.admin_user
        )
        
        UserAttribute.objects.create(
            user=self.test_user,
            name='a_attr',
            value='3',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-user-attributes', kwargs={'pk': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Verify we have all 3 attributes
        self.assertEqual(len(data), 3)
        
        # Check that attributes are present with correct values
        attr_by_name_service = {(attr['name'], attr.get('service_name')): attr for attr in data}
        
        # Global attributes (no service)
        self.assertIn(('a_attr', None), attr_by_name_service)
        self.assertIn(('z_attr', None), attr_by_name_service)
        
        # Service-specific attribute
        self.assertIn(('a_attr', 'billing_api'), attr_by_name_service)
        
        # Verify values
        self.assertEqual(attr_by_name_service[('a_attr', None)]['value'], '3')
        self.assertEqual(attr_by_name_service[('z_attr', None)]['value'], '1')
        self.assertEqual(attr_by_name_service[('a_attr', 'billing_api')]['value'], '2')