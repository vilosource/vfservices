"""
Integration test for roles API user_count field
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from identity_app.models import Service, Role, UserRole
from common.jwt_auth.utils import generate_jwt_token


class RolesAPIIntegrationTest(TestCase):
    """Test that roles API returns correct user counts"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create services
        self.identity_service = Service.objects.create(
            name='identity_provider',
            display_name='Identity Provider',
            description='Identity service'
        )
        
        # Create roles
        self.identity_admin_role = Role.objects.create(
            name='identity_admin',
            display_name='Identity Admin',
            service=self.identity_service,
            is_global=True
        )
        
        self.identity_viewer_role = Role.objects.create(
            name='identity_viewer',
            display_name='Identity Viewer',
            service=self.identity_service,
            is_global=True
        )
        
        # Create admin user with identity_admin role
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='adminpass'
        )
        UserRole.objects.create(
            user=self.admin_user,
            role=self.identity_admin_role,
            granted_by=self.admin_user
        )
        
        # Create alice with identity_admin role
        self.alice = User.objects.create_user(
            username='alice',
            email='alice@test.com',
            password='alicepass'
        )
        UserRole.objects.create(
            user=self.alice,
            role=self.identity_admin_role,
            granted_by=self.admin_user
        )
        
        # Create bob with identity_viewer role
        self.bob = User.objects.create_user(
            username='bob',
            email='bob@test.com',
            password='bobpass'
        )
        UserRole.objects.create(
            user=self.bob,
            role=self.identity_viewer_role,
            granted_by=self.admin_user
        )
        
        # Authenticate
        self.token = generate_jwt_token(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    
    def test_roles_api_includes_user_count(self):
        """Test that all roles have user_count field"""
        response = self.client.get('/api/admin/roles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        self.assertGreater(len(roles), 0)
        
        # Check all roles have user_count
        for role in roles:
            self.assertIn('user_count', role, 
                         f"Role {role.get('name')} missing user_count field")
            self.assertIsInstance(role['user_count'], int)
            self.assertGreaterEqual(role['user_count'], 0)
    
    def test_identity_admin_user_count(self):
        """Test identity_admin role has correct count"""
        response = self.client.get('/api/admin/roles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        identity_admin = next(
            (r for r in roles if r['name'] == 'identity_admin'),
            None
        )
        
        self.assertIsNotNone(identity_admin)
        self.assertEqual(identity_admin['user_count'], 2,
                        "identity_admin should have 2 users (admin and alice)")
    
    def test_identity_viewer_user_count(self):
        """Test identity_viewer role has correct count"""
        response = self.client.get('/api/admin/roles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        roles = response.json()
        identity_viewer = next(
            (r for r in roles if r['name'] == 'identity_viewer'),
            None
        )
        
        self.assertIsNotNone(identity_viewer)
        self.assertEqual(identity_viewer['user_count'], 1,
                        "identity_viewer should have 1 user (bob)")
    
    def test_user_count_updates_on_assignment(self):
        """Test user_count updates when roles are assigned"""
        # Get initial count
        response = self.client.get('/api/admin/roles/')
        roles = response.json()
        identity_viewer = next(r for r in roles if r['name'] == 'identity_viewer')
        initial_count = identity_viewer['user_count']
        
        # Create new user and assign role
        charlie = User.objects.create_user(
            username='charlie',
            email='charlie@test.com'
        )
        UserRole.objects.create(
            user=charlie,
            role=self.identity_viewer_role,
            granted_by=self.admin_user
        )
        
        # Check updated count
        response = self.client.get('/api/admin/roles/')
        roles = response.json()
        identity_viewer = next(r for r in roles if r['name'] == 'identity_viewer')
        
        self.assertEqual(identity_viewer['user_count'], initial_count + 1)