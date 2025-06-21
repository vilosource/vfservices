"""
Tests for Service Attributes API endpoints
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from ..models import Service, Role, UserRole, ServiceAttribute, UserAttribute


class ServiceAttributesAPITestCase(TestCase):
    """Test cases for service attributes API endpoints."""
    
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
            password='testuser123!#QWERT'
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
    
    def test_list_service_attributes_empty(self):
        """Test listing attributes when service has none."""
        url = reverse('admin-attribute-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data, [])
    
    def test_list_service_attributes_with_data(self):
        """Test listing service attributes."""
        # Create some attributes
        attr1 = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='department',
            display_name='Department',
            description='User department',
            attribute_type='string',
            is_required=False
        )
        
        attr2 = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='access_level',
            display_name='Access Level',
            description='User access level',
            attribute_type='integer',
            is_required=True,
            default_value='1'
        )
        
        url = reverse('admin-attribute-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 2)
        
        # Check attributes are ordered by service name, then attribute name
        self.assertEqual(data[0]['name'], 'access_level')
        self.assertEqual(data[1]['name'], 'department')
    
    def test_list_attributes_filter_by_service(self):
        """Test filtering attributes by service."""
        # Create attributes for different services
        ServiceAttribute.objects.create(
            service=self.identity_service,
            name='role_scope',
            display_name='Role Scope',
            attribute_type='string'
        )
        
        ServiceAttribute.objects.create(
            service=self.billing_service,
            name='billing_tier',
            display_name='Billing Tier',
            attribute_type='string'
        )
        
        url = reverse('admin-attribute-list')
        response = self.client.get(url, {'service': 'billing_api'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['service_name'], 'billing_api')
    
    def test_get_attribute_detail(self):
        """Test getting attribute details."""
        attr = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='department',
            display_name='Department',
            attribute_type='string'
        )
        
        url = reverse('admin-attribute-detail', kwargs={'pk': attr.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['name'], 'department')
        self.assertEqual(data['service'], self.billing_service.id)
        self.assertEqual(data['service_name'], 'billing_api')
    
    def test_create_service_attribute(self):
        """Test creating a new service attribute."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'location',
            'display_name': 'Location',
            'description': 'User location',
            'attribute_type': 'string',
            'is_required': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['name'], 'location')
        self.assertEqual(response_data['service'], self.billing_service.id)
        self.assertEqual(response_data['attribute_type'], 'string')
        
        # Verify attribute was created
        attr = ServiceAttribute.objects.get(
            service=self.billing_service,
            name='location'
        )
        self.assertEqual(attr.display_name, 'Location')
    
    def test_create_attribute_with_default_value(self):
        """Test creating attribute with default value."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'max_users',
            'display_name': 'Max Users',
            'description': 'Maximum number of users',
            'attribute_type': 'integer',
            'is_required': True,
            'default_value': '10'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['default_value'], '10')
    
    def test_create_attribute_invalid_name(self):
        """Test creating attribute with invalid name format."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'Invalid-Name',  # Contains uppercase and hyphen
            'display_name': 'Invalid',
            'attribute_type': 'string'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.json())
    
    def test_create_attribute_duplicate_name(self):
        """Test creating attribute with duplicate name for same service."""
        # Create initial attribute
        ServiceAttribute.objects.create(
            service=self.billing_service,
            name='department',
            display_name='Department',
            attribute_type='string'
        )
        
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'department',
            'display_name': 'Department 2',
            'attribute_type': 'string'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already exists', response.json()['error'])
    
    def test_create_attribute_invalid_default_value(self):
        """Test creating attribute with invalid default value for type."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'count',
            'display_name': 'Count',
            'attribute_type': 'integer',
            'default_value': 'not_a_number'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_data = response.json()
        # The error might be in a nested structure
        self.assertTrue(
            'default_value' in error_data or 
            ('non_field_errors' in error_data and 'default value' in str(error_data).lower()),
            f"Expected default_value error, got: {error_data}"
        )
    
    def test_create_list_attribute_with_valid_default(self):
        """Test creating list attribute with valid JSON default."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': self.billing_service.id,
            'name': 'tags',
            'display_name': 'Tags',
            'attribute_type': 'list_string',
            'default_value': '["tag1", "tag2"]'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['default_value'], '["tag1", "tag2"]')
    
    def test_update_service_attribute(self):
        """Test updating a service attribute."""
        attr = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='department',
            display_name='Department',
            description='User department',
            attribute_type='string',
            is_required=False
        )
        
        url = reverse('admin-attribute-detail', kwargs={'pk': attr.id})
        data = {
            'display_name': 'Department Name',
            'description': 'Updated description',
            'is_required': True
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        self.assertEqual(response_data['display_name'], 'Department Name')
        self.assertEqual(response_data['is_required'], True)
        
        # Verify attribute was updated
        attr.refresh_from_db()
        self.assertEqual(attr.description, 'Updated description')
    
    def test_delete_service_attribute(self):
        """Test deleting a service attribute."""
        attr = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='temp_attr',
            display_name='Temporary',
            attribute_type='string'
        )
        
        url = reverse('admin-attribute-detail', kwargs={'pk': attr.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify attribute was deleted
        self.assertFalse(
            ServiceAttribute.objects.filter(id=attr.id).exists()
        )
    
    def test_cannot_delete_attribute_with_users(self):
        """Test that attributes with user data cannot be deleted."""
        attr = ServiceAttribute.objects.create(
            service=self.billing_service,
            name='department',
            display_name='Department',
            attribute_type='string'
        )
        
        # Create user attribute
        UserAttribute.objects.create(
            user=self.test_user,
            service=self.billing_service,
            name='department',
            value='Sales',
            updated_by=self.admin_user
        )
        
        url = reverse('admin-attribute-detail', kwargs={'pk': attr.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('1 users have this attribute', response.json()['error'])
        
        # Verify attribute still exists
        self.assertTrue(
            ServiceAttribute.objects.filter(id=attr.id).exists()
        )
    
    def test_requires_admin_permission(self):
        """Test that attribute endpoints require admin permission."""
        # Authenticate as non-admin user
        self.mock_jwt_auth.return_value = (self.test_user, None)
        
        # Mock RBACService to return no admin role
        with patch('identity_app.permissions.RBACService.get_user_roles') as mock_get_roles:
            mock_get_roles.return_value = []
            
            # Test list attributes
            url = reverse('admin-attribute-list')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            
            # Test create attribute
            response = self.client.post(url, {
                'service_id': 1,
                'name': 'test',
                'display_name': 'Test',
                'attribute_type': 'string'
            })
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_attribute_type_validation(self):
        """Test various attribute type validations."""
        url = reverse('admin-attribute-list')
        
        # Test boolean default value
        data = {
            'service_id': self.billing_service.id,
            'name': 'is_active',
            'display_name': 'Is Active',
            'attribute_type': 'boolean',
            'default_value': 'true'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test invalid boolean default
        data['name'] = 'is_enabled'
        data['default_value'] = 'yes'  # Invalid for boolean
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test list_integer validation
        data = {
            'service_id': self.billing_service.id,
            'name': 'user_ids',
            'display_name': 'User IDs',
            'attribute_type': 'list_integer',
            'default_value': '[1, 2, 3]'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test invalid list_integer (contains string)
        data['name'] = 'invalid_ids'
        data['default_value'] = '[1, "two", 3]'
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_service_not_found(self):
        """Test creating attribute with non-existent service."""
        url = reverse('admin-attribute-list')
        data = {
            'service_id': 99999,
            'name': 'test',
            'display_name': 'Test',
            'attribute_type': 'string'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.json()['error'], 'Service not found')
    
    def test_missing_service_id(self):
        """Test creating attribute without service_id."""
        url = reverse('admin-attribute-list')
        data = {
            'name': 'test',
            'display_name': 'Test',
            'attribute_type': 'string'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()['error'], 'service_id is required')