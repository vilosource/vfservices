"""
Tests for RBAC-ABAC services
"""

from unittest.mock import patch, Mock, MagicMock
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from identity_app.models import (
    Service, Role, UserRole, ServiceAttribute, UserAttribute
)
from identity_app.services import (
    RBACService, AttributeService, RedisService, ManifestService
)


class RBACServiceTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass')
        self.service = Service.objects.create(name='test_service', display_name='Test')
        self.role = Role.objects.create(
            service=self.service,
            name='editor',
            display_name='Editor'
        )
    
    def test_get_user_roles(self):
        """Test getting user roles."""
        # No roles initially
        roles = RBACService.get_user_roles(self.user)
        self.assertEqual(len(roles), 0)
        
        # Assign role
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin
        )
        
        roles = RBACService.get_user_roles(self.user)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0], user_role)
        
        # Filter by service
        other_service = Service.objects.create(name='other', display_name='Other')
        other_role = Role.objects.create(service=other_service, name='viewer', display_name='Viewer')
        UserRole.objects.create(
            user=self.user,
            role=other_role,
            granted_by=self.admin
        )
        
        roles = RBACService.get_user_roles(self.user, self.service)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0].role, self.role)
    
    def test_get_user_roles_excludes_expired(self):
        """Test that expired roles are excluded."""
        # Active role
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Expired role
        expired_role = Role.objects.create(service=self.service, name='expired', display_name='Expired')
        UserRole.objects.create(
            user=self.user,
            role=expired_role,
            granted_by=self.admin,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        roles = RBACService.get_user_roles(self.user)
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0].role.name, 'editor')
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    @patch('identity_app.services.RedisService.populate_user_attributes')
    def test_assign_role(self, mock_populate, mock_invalidate):
        """Test assigning a role."""
        user_role = RBACService.assign_role(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            resource_id='doc_123',
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        self.assertEqual(user_role.user, self.user)
        self.assertEqual(user_role.role, self.role)
        self.assertEqual(user_role.resource_id, 'doc_123')
        self.assertIsNotNone(user_role.expires_at)
        
        # Check Redis invalidation was called
        mock_invalidate.assert_called_once_with(self.user.id, self.service.name)
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    @patch('identity_app.services.RedisService.populate_user_attributes')
    def test_revoke_role(self, mock_populate, mock_invalidate):
        """Test revoking a role."""
        # Create role assignment
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin
        )
        
        # Revoke it
        RBACService.revoke_role(self.user, self.role)
        
        # Check it's gone
        self.assertEqual(UserRole.objects.filter(user=self.user).count(), 0)
        
        # Check Redis invalidation
        mock_invalidate.assert_called_once_with(self.user.id, self.service.name)


class AttributeServiceTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass')
        self.service = Service.objects.create(name='test_service', display_name='Test')
    
    def test_get_user_attributes_empty(self):
        """Test getting attributes when none exist."""
        attrs = AttributeService.get_user_attributes(self.user)
        self.assertEqual(attrs, {})
    
    def test_get_user_attributes_global(self):
        """Test getting global attributes."""
        # Create global attribute
        attr = UserAttribute.objects.create(
            user=self.user,
            name='department',
            value='"Engineering"'
        )
        
        attrs = AttributeService.get_user_attributes(self.user)
        self.assertEqual(attrs, {'department': 'Engineering'})
    
    def test_get_user_attributes_with_service(self):
        """Test getting service-specific attributes."""
        # Global attribute
        UserAttribute.objects.create(
            user=self.user,
            name='department',
            value='"Engineering"'
        )
        
        # Service attribute
        UserAttribute.objects.create(
            user=self.user,
            service=self.service,
            name='access_level',
            value='3'
        )
        
        attrs = AttributeService.get_user_attributes(self.user, self.service)
        self.assertEqual(attrs, {
            'department': 'Engineering',
            'access_level': '3'
        })
    
    def test_get_user_attributes_with_defaults(self):
        """Test default values for required attributes."""
        # Create required attribute with default
        ServiceAttribute.objects.create(
            service=self.service,
            name='role_level',
            display_name='Role Level',
            attribute_type='integer',
            is_required=True,
            default_value='1'
        )
        
        attrs = AttributeService.get_user_attributes(self.user, self.service)
        self.assertEqual(attrs, {'role_level': 1})
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    def test_set_user_attribute(self, mock_invalidate):
        """Test setting a user attribute."""
        attr = AttributeService.set_user_attribute(
            user=self.user,
            name='department',
            value='Sales',
            service=self.service,
            updated_by=self.admin
        )
        
        self.assertEqual(attr.user, self.user)
        self.assertEqual(attr.name, 'department')
        self.assertEqual(attr.get_value(), 'Sales')
        self.assertEqual(attr.service, self.service)
        self.assertEqual(attr.updated_by, self.admin)
        
        # Check Redis invalidation
        mock_invalidate.assert_called_once_with(self.user.id, self.service.name)


class RedisServiceTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.service = Service.objects.create(name='test_service', display_name='Test')
        self.role = Role.objects.create(
            service=self.service,
            name='editor',
            display_name='Editor'
        )
    
    @patch('identity_app.services.RedisAttributeClient')
    def test_get_client(self, mock_client_class):
        """Test getting Redis client singleton."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Clear any existing client
        if hasattr(RedisService, '_client'):
            delattr(RedisService, '_client')
        
        client1 = RedisService.get_client()
        client2 = RedisService.get_client()
        
        # Should be same instance
        self.assertEqual(client1, client2)
        mock_client_class.assert_called_once()
    
    @patch('identity_app.services.RedisService.get_client')
    def test_populate_user_attributes(self, mock_get_client):
        """Test populating user attributes in Redis."""
        # Setup mock Redis client
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.set_user_attributes.return_value = True
        
        # Create user data
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.user
        )
        UserAttribute.objects.create(
            user=self.user,
            name='department',
            value='"Engineering"'
        )
        
        # Populate
        result = RedisService.populate_user_attributes(self.user.id, self.service.name)
        
        self.assertTrue(result)
        mock_client.set_user_attributes.assert_called_once()
        
        # Check the attributes passed
        call_args = mock_client.set_user_attributes.call_args
        user_attrs = call_args[0][2]  # Third argument
        self.assertEqual(user_attrs.user_id, self.user.id)
        self.assertEqual(user_attrs.username, 'testuser')
        self.assertEqual(user_attrs.roles, ['editor'])
        self.assertEqual(user_attrs.department, 'Engineering')
    
    @patch('identity_app.services.RedisService.get_client')
    def test_invalidate_user_cache(self, mock_get_client):
        """Test invalidating user cache."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.invalidate_user_attributes.return_value = 2
        
        RedisService.invalidate_user_cache(123, 'test_service')
        
        mock_client.invalidate_user_attributes.assert_called_once_with(123, 'test_service')
        mock_client.publish_invalidation.assert_called_once_with(123, 'test_service')


class ManifestServiceTest(TestCase):
    
    def setUp(self):
        self.manifest_data = {
            'service': 'new_service',
            'display_name': 'New Service',
            'description': 'A new service',
            'version': '1.0',
            'roles': [
                {
                    'name': 'admin',
                    'display_name': 'Administrator',
                    'description': 'Full access',
                    'is_global': True
                },
                {
                    'name': 'viewer',
                    'display_name': 'Viewer',
                    'description': 'Read only access'
                }
            ],
            'attributes': [
                {
                    'name': 'department',
                    'display_name': 'Department',
                    'description': 'User department',
                    'type': 'string',
                    'required': True,
                    'default': 'General'
                },
                {
                    'name': 'access_level',
                    'display_name': 'Access Level',
                    'type': 'integer',
                    'required': False
                }
            ]
        }
    
    @patch('identity_app.services.RedisService.populate_all_users_for_service')
    def test_register_manifest_new_service(self, mock_populate):
        """Test registering manifest for new service."""
        manifest = ManifestService.register_manifest(
            self.manifest_data,
            ip_address='192.168.1.1'
        )
        
        # Check service created
        service = Service.objects.get(name='new_service')
        self.assertEqual(service.display_name, 'New Service')
        self.assertEqual(service.description, 'A new service')
        
        # Check manifest
        self.assertEqual(manifest.service, service)
        self.assertEqual(manifest.version, 1)
        self.assertTrue(manifest.is_active)
        self.assertEqual(manifest.submitted_by_ip, '192.168.1.1')
        
        # Check roles created
        roles = Role.objects.filter(service=service).order_by('name')
        self.assertEqual(roles.count(), 2)
        self.assertEqual(roles[0].name, 'admin')
        self.assertEqual(roles[1].name, 'viewer')
        
        # Check attributes created
        attrs = ServiceAttribute.objects.filter(service=service).order_by('name')
        self.assertEqual(attrs.count(), 2)
        self.assertEqual(attrs[1].name, 'department')
        self.assertEqual(attrs[1].get_default_value(), 'General')
        
        # Check Redis population called
        mock_populate.assert_called_once_with('new_service')
    
    @patch('identity_app.services.RedisService.populate_all_users_for_service')
    def test_register_manifest_update_service(self, mock_populate):
        """Test updating existing service manifest."""
        # Create existing service
        service = Service.objects.create(
            name='new_service',
            display_name='Old Name'
        )
        
        # Register first manifest
        first_manifest = ManifestService.register_manifest(self.manifest_data)
        self.assertEqual(first_manifest.version, 1)
        self.assertTrue(first_manifest.is_active)
        
        # Update manifest data
        updated_data = self.manifest_data.copy()
        updated_data['display_name'] = 'Updated Service'
        updated_data['roles'].append({
            'name': 'editor',
            'display_name': 'Editor'
        })
        
        # Register updated manifest
        second_manifest = ManifestService.register_manifest(updated_data)
        
        # Check version incremented
        self.assertEqual(second_manifest.version, 2)
        self.assertTrue(second_manifest.is_active)
        
        # Check first manifest deactivated
        first_manifest.refresh_from_db()
        self.assertFalse(first_manifest.is_active)
        
        # Check service updated
        service.refresh_from_db()
        self.assertEqual(service.display_name, 'Updated Service')
        
        # Check new role added
        self.assertEqual(Role.objects.filter(service=service).count(), 3)
    
    def test_register_manifest_invalid_data(self):
        """Test registering manifest with invalid data."""
        # Missing service name
        invalid_data = {'roles': []}
        
        with self.assertRaises(ValueError) as context:
            ManifestService.register_manifest(invalid_data)
        
        self.assertIn('service', str(context.exception))