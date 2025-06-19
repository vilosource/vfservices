"""
Tests for RBAC-ABAC models
"""

import json
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from identity_app.models import (
    Service, Role, UserRole, ServiceAttribute, 
    UserAttribute, ServiceManifest
)


class ServiceModelTest(TestCase):
    
    def test_create_service(self):
        """Test creating a service."""
        service = Service.objects.create(
            name='test_service',
            display_name='Test Service',
            description='A test service'
        )
        
        self.assertEqual(str(service), 'Test Service (test_service)')
        self.assertTrue(service.is_active)
        self.assertEqual(service.manifest_version, '1.0')
    
    def test_service_name_validation(self):
        """Test service name validation."""
        # Valid names
        valid_names = ['billing_api', 'inventory-api', 'web2']
        for name in valid_names:
            service = Service(name=name, display_name=name)
            service.full_clean()  # Should not raise
        
        # Invalid names
        invalid_names = ['Test', '2service', 'service!', 'my service']
        for name in invalid_names:
            service = Service(name=name, display_name=name)
            with self.assertRaises(Exception):
                service.full_clean()


class RoleModelTest(TestCase):
    
    def setUp(self):
        self.service = Service.objects.create(
            name='test_service',
            display_name='Test Service'
        )
    
    def test_create_role(self):
        """Test creating a role."""
        role = Role.objects.create(
            service=self.service,
            name='admin',
            display_name='Administrator',
            description='Full access'
        )
        
        self.assertEqual(str(role), 'test_service:admin')
        self.assertEqual(role.full_name, 'test_service_admin')
        self.assertTrue(role.is_global)
    
    def test_role_uniqueness(self):
        """Test role name uniqueness within service."""
        Role.objects.create(
            service=self.service,
            name='editor',
            display_name='Editor'
        )
        
        # Should fail - duplicate name in same service
        with self.assertRaises(Exception):
            Role.objects.create(
                service=self.service,
                name='editor',
                display_name='Another Editor'
            )
        
        # Should succeed - same name in different service
        other_service = Service.objects.create(name='other_service', display_name='Other')
        Role.objects.create(
            service=other_service,
            name='editor',
            display_name='Editor'
        )


class UserRoleModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass')
        self.service = Service.objects.create(name='test_service', display_name='Test')
        self.role = Role.objects.create(
            service=self.service,
            name='editor',
            display_name='Editor'
        )
    
    def test_assign_role(self):
        """Test assigning a role to a user."""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin
        )
        
        self.assertEqual(
            str(user_role), 
            'testuser has test_service:editor'
        )
        self.assertTrue(user_role.is_active)
        self.assertFalse(user_role.is_expired)
    
    def test_scoped_role(self):
        """Test resource-scoped role assignment."""
        user_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            resource_id='doc_123'
        )
        
        self.assertEqual(
            str(user_role), 
            'testuser has test_service:editor (resource: doc_123)'
        )
    
    def test_role_expiration(self):
        """Test role expiration."""
        # Create expired role
        expired_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        self.assertTrue(expired_role.is_expired)
        self.assertFalse(expired_role.is_active)
        
        # Create future role
        future_role = UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            resource_id='doc_456',
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        self.assertFalse(future_role.is_expired)
        self.assertTrue(future_role.is_active)
    
    def test_role_uniqueness(self):
        """Test preventing duplicate role assignments."""
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin
        )
        
        # Should fail - duplicate assignment
        with self.assertRaises(Exception):
            UserRole.objects.create(
                user=self.user,
                role=self.role,
                granted_by=self.admin
            )
        
        # Should succeed - different resource_id
        UserRole.objects.create(
            user=self.user,
            role=self.role,
            granted_by=self.admin,
            resource_id='doc_123'
        )


class ServiceAttributeModelTest(TestCase):
    
    def setUp(self):
        self.service = Service.objects.create(
            name='test_service',
            display_name='Test Service'
        )
    
    def test_create_attribute(self):
        """Test creating a service attribute."""
        attr = ServiceAttribute.objects.create(
            service=self.service,
            name='department',
            display_name='Department',
            description='User department',
            attribute_type='string',
            is_required=True,
            default_value='"Engineering"'
        )
        
        self.assertEqual(str(attr), 'test_service:department')
        self.assertEqual(attr.get_default_value(), 'Engineering')
    
    def test_attribute_types(self):
        """Test different attribute types."""
        test_cases = [
            ('string', '"test"', 'test'),
            ('integer', '42', 42),
            ('boolean', 'true', True),
            ('list_string', '["a", "b", "c"]', ['a', 'b', 'c']),
            ('list_integer', '[1, 2, 3]', [1, 2, 3]),
            ('json', '{"key": "value"}', {'key': 'value'}),
        ]
        
        for attr_type, default_value, expected in test_cases:
            attr = ServiceAttribute.objects.create(
                service=self.service,
                name=f'attr_{attr_type}',
                display_name=f'Attr {attr_type}',
                attribute_type=attr_type,
                default_value=default_value
            )
            
            self.assertEqual(attr.get_default_value(), expected)


class UserAttributeModelTest(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'pass')
        self.admin = User.objects.create_user('admin', 'admin@example.com', 'pass')
        self.service = Service.objects.create(name='test_service', display_name='Test')
    
    def test_global_attribute(self):
        """Test creating a global user attribute."""
        attr = UserAttribute.objects.create(
            user=self.user,
            name='department',
            updated_by=self.admin
        )
        attr.set_value('Engineering')
        attr.save()
        
        self.assertEqual(str(attr), 'testuser - global:department')
        self.assertEqual(attr.get_value(), 'Engineering')
    
    def test_service_attribute(self):
        """Test creating a service-specific attribute."""
        attr = UserAttribute.objects.create(
            user=self.user,
            service=self.service,
            name='role_level',
            updated_by=self.admin
        )
        attr.set_value(3)
        attr.save()
        
        self.assertEqual(str(attr), 'testuser - test_service:role_level')
        self.assertEqual(attr.get_value(), '3')  # Stored as string
    
    def test_complex_attribute_values(self):
        """Test storing complex attribute values."""
        attr = UserAttribute.objects.create(
            user=self.user,
            name='permissions',
            updated_by=self.admin
        )
        
        # Test list
        attr.set_value(['read', 'write', 'delete'])
        attr.save()
        self.assertEqual(attr.get_value(), ['read', 'write', 'delete'])
        
        # Test dict
        attr.set_value({'can_edit': True, 'max_size': 1000})
        attr.save()
        self.assertEqual(attr.get_value(), {'can_edit': True, 'max_size': 1000})
    
    def test_attribute_uniqueness(self):
        """Test attribute uniqueness per user/service/name."""
        UserAttribute.objects.create(
            user=self.user,
            service=self.service,
            name='level',
            value='5'
        )
        
        # Should fail - duplicate
        with self.assertRaises(Exception):
            UserAttribute.objects.create(
                user=self.user,
                service=self.service,
                name='level',
                value='10'
            )
        
        # Should succeed - different service
        other_service = Service.objects.create(name='other', display_name='Other')
        UserAttribute.objects.create(
            user=self.user,
            service=other_service,
            name='level',
            value='10'
        )


class ServiceManifestModelTest(TestCase):
    
    def setUp(self):
        self.service = Service.objects.create(
            name='test_service',
            display_name='Test Service'
        )
    
    def test_create_manifest(self):
        """Test creating a service manifest."""
        manifest_data = {
            'service': 'test_service',
            'version': '1.0',
            'roles': [
                {'name': 'admin', 'description': 'Administrator'},
                {'name': 'user', 'description': 'Regular user'}
            ],
            'attributes': [
                {'name': 'department', 'type': 'string', 'required': True}
            ]
        }
        
        manifest = ServiceManifest.objects.create(
            service=self.service,
            version=1,
            manifest_data=manifest_data,
            submitted_by_ip='127.0.0.1'
        )
        
        self.assertEqual(str(manifest), 'test_service manifest v1')
        self.assertTrue(manifest.is_active)
        self.assertEqual(manifest.manifest_data['service'], 'test_service')
    
    def test_manifest_versioning(self):
        """Test manifest version management."""
        # Create first manifest
        manifest1 = ServiceManifest.objects.create(
            service=self.service,
            version=1,
            manifest_data={'service': 'test_service', 'v': 1}
        )
        self.assertTrue(manifest1.is_active)
        
        # Create second manifest
        manifest2 = ServiceManifest.objects.create(
            service=self.service,
            version=2,
            manifest_data={'service': 'test_service', 'v': 2}
        )
        
        # Manually deactivate first (normally done by service)
        manifest1.is_active = False
        manifest1.save()
        
        # Check only latest is active
        active_manifests = ServiceManifest.objects.filter(
            service=self.service,
            is_active=True
        )
        self.assertEqual(active_manifests.count(), 1)
        self.assertEqual(active_manifests.first().version, 2)