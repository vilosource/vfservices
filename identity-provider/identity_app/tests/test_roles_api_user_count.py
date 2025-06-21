"""
Test the roles API endpoint to ensure user_count is correctly returned.
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from identity_app.utils import generate_jwt_token

from identity_app.models import Service, Role, UserRole


class RolesAPIUserCountTest(TestCase):
    """Test that the roles API correctly returns user counts."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass123'
        )
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        # Create test users
        self.alice = User.objects.create_user(
            username='alice',
            email='alice@test.com',
            password='alicepass123'
        )
        
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@test.com',
            password='bobpass123'
        )
        
        self.charlie = User.objects.create_user(
            username='charlie',
            email='charlie@test.com',
            password='charliepass123'
        )
        
        # Create services
        self.identity_service = Service.objects.create(
            name='identity_provider',
            display_name='Identity Provider',
            description='Identity management service',
            is_active=True
        )
        
        self.billing_service = Service.objects.create(
            name='billing_api',
            display_name='Billing API',
            description='Billing service',
            is_active=True
        )
        
        # Create roles
        self.identity_admin_role = Role.objects.create(
            service=self.identity_service,
            name='identity_admin',
            display_name='Identity Admin',
            description='Can manage users and roles',
            is_global=True
        )
        
        self.identity_viewer_role = Role.objects.create(
            service=self.identity_service,
            name='identity_viewer',
            display_name='Identity Viewer',
            description='Can view users and roles',
            is_global=True
        )
        
        self.billing_admin_role = Role.objects.create(
            service=self.billing_service,
            name='billing_admin',
            display_name='Billing Admin',
            description='Can manage billing',
            is_global=True
        )
        
        # Assign roles to users
        # Alice has identity_admin
        UserRole.objects.create(
            user=self.alice,
            role=self.identity_admin_role,
            granted_by=self.admin_user
        )
        
        # Bob has identity_admin and billing_admin
        UserRole.objects.create(
            user=self.bob,
            role=self.identity_admin_role,
            granted_by=self.admin_user
        )
        UserRole.objects.create(
            user=self.bob,
            role=self.billing_admin_role,
            granted_by=self.admin_user
        )
        
        # Charlie has billing_admin
        UserRole.objects.create(
            user=self.charlie,
            role=self.billing_admin_role,
            granted_by=self.admin_user
        )
        
        # No one has identity_viewer role
        
        # Give admin user the identity_admin role
        UserRole.objects.create(
            user=self.admin_user,
            role=self.identity_admin_role,
            granted_by=self.admin_user
        )
        
        # Authenticate as admin
        self._authenticate_as_admin()
    
    def _authenticate_as_admin(self):
        """Helper to authenticate as admin user."""
        token = generate_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_roles_api_returns_user_count(self):
        """Test that the roles API returns user_count field."""
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        self.assertIsInstance(roles, list)
        self.assertGreater(len(roles), 0)
        
        # Check that all roles have user_count field
        for role in roles:
            self.assertIn('user_count', role, f"Role {role.get('name')} missing user_count field")
            self.assertIsInstance(role['user_count'], int, f"user_count should be an integer for role {role.get('name')}")
    
    def test_identity_admin_role_user_count(self):
        """Test that identity_admin role has correct user count."""
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # Find identity_admin role
        identity_admin = None
        for role in roles:
            if role.get('name') == 'identity_admin' and role.get('service_name') == 'identity_provider':
                identity_admin = role
                break
        
        self.assertIsNotNone(identity_admin, "identity_admin role not found in response")
        self.assertEqual(identity_admin['user_count'], 3, "identity_admin should have 3 users (alice, bob, admin)")
    
    def test_billing_admin_role_user_count(self):
        """Test that billing_admin role has correct user count."""
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # Find billing_admin role
        billing_admin = None
        for role in roles:
            if role.get('name') == 'billing_admin' and role.get('service_name') == 'billing_api':
                billing_admin = role
                break
        
        self.assertIsNotNone(billing_admin, "billing_admin role not found in response")
        self.assertEqual(billing_admin['user_count'], 2, "billing_admin should have 2 users (bob, charlie)")
    
    def test_identity_viewer_role_user_count(self):
        """Test that identity_viewer role has zero user count."""
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # Find identity_viewer role
        identity_viewer = None
        for role in roles:
            if role.get('name') == 'identity_viewer' and role.get('service_name') == 'identity_provider':
                identity_viewer = role
                break
        
        self.assertIsNotNone(identity_viewer, "identity_viewer role not found in response")
        self.assertEqual(identity_viewer['user_count'], 0, "identity_viewer should have 0 users")
    
    def test_role_structure(self):
        """Test that role objects have the expected structure."""
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        self.assertGreater(len(roles), 0)
        
        # Check first role structure
        role = roles[0]
        expected_fields = [
            'id', 'name', 'display_name', 'description', 
            'is_global', 'service_name', 'service_display_name',
            'created_at', 'user_count'
        ]
        
        for field in expected_fields:
            self.assertIn(field, role, f"Role missing expected field: {field}")
    
    def test_filter_by_service(self):
        """Test filtering roles by service."""
        url = reverse('admin-roles-list')
        response = self.client.get(url, {'service': 'identity_provider'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # All roles should be from identity_provider service
        for role in roles:
            self.assertEqual(role['service_name'], 'identity_provider')
        
        # Should have identity_admin and identity_viewer
        role_names = [r['name'] for r in roles]
        self.assertIn('identity_admin', role_names)
        self.assertIn('identity_viewer', role_names)
    
    def test_filter_by_is_global(self):
        """Test filtering roles by is_global flag."""
        url = reverse('admin-roles-list')
        response = self.client.get(url, {'is_global': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # All roles should be global
        for role in roles:
            self.assertTrue(role['is_global'])
    
    def test_user_count_updates_when_role_assigned(self):
        """Test that user_count updates when a role is assigned."""
        # Get initial count
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        roles = response.json()
        
        # Find identity_viewer role initial count
        identity_viewer = next(
            (r for r in roles if r['name'] == 'identity_viewer' and r['service_name'] == 'identity_provider'),
            None
        )
        initial_count = identity_viewer['user_count']
        self.assertEqual(initial_count, 0)
        
        # Assign identity_viewer to alice
        UserRole.objects.create(
            user=self.alice,
            role=self.identity_viewer_role,
            granted_by=self.admin_user
        )
        
        # Check count again
        response = self.client.get(url)
        roles = response.json()
        
        identity_viewer = next(
            (r for r in roles if r['name'] == 'identity_viewer' and r['service_name'] == 'identity_provider'),
            None
        )
        new_count = identity_viewer['user_count']
        self.assertEqual(new_count, 1, "User count should increase by 1 after assignment")
    
    def test_inactive_service_roles_not_included(self):
        """Test that roles from inactive services are not included."""
        # Create inactive service with role
        inactive_service = Service.objects.create(
            name='inactive_service',
            display_name='Inactive Service',
            is_active=False
        )
        
        Role.objects.create(
            service=inactive_service,
            name='inactive_role',
            display_name='Inactive Role'
        )
        
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        
        # Should not include role from inactive service
        role_names = [f"{r['service_name']}:{r['name']}" for r in roles]
        self.assertNotIn('inactive_service:inactive_role', role_names)
    
    def test_expired_role_assignments_not_counted(self):
        """Test that expired role assignments are not counted."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create a new user with an expired role
        expired_user = User.objects.create_user(
            username='expired_user',
            email='expired@test.com'
        )
        
        # Assign identity_viewer with past expiration
        UserRole.objects.create(
            user=expired_user,
            role=self.identity_viewer_role,
            granted_by=self.admin_user,
            expires_at=timezone.now() - timedelta(days=1)  # Expired yesterday
        )
        
        url = reverse('admin-roles-list')
        response = self.client.get(url)
        
        roles = response.json()
        
        # Find identity_viewer role
        identity_viewer = next(
            (r for r in roles if r['name'] == 'identity_viewer' and r['service_name'] == 'identity_provider'),
            None
        )
        
        # Should still be 0 because the assignment is expired
        self.assertEqual(identity_viewer['user_count'], 0, "Expired assignments should not be counted")