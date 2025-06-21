"""
Tests for Identity Provider Admin API
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta
import json

from identity_app.models import Service, Role, UserRole
from identity_app.services import RBACService, RedisService
from common.jwt_auth.utils import generate_jwt_token


class AdminAPITestCase(TestCase):
    """Base test case with common setup"""
    
    def setUp(self):
        """Set up test data"""
        # Create identity provider service
        self.identity_service = Service.objects.create(
            name='identity_provider',
            display_name='Identity Provider',
            description='Core identity service'
        )
        
        # Create identity_admin role
        self.admin_role = Role.objects.create(
            name='identity_admin',
            display_name='Identity Administrator',
            service=self.identity_service,
            is_global=True
        )
        
        # Create test services and roles
        self.billing_service = Service.objects.create(
            name='billing_api',
            display_name='Billing API',
            description='Billing service'
        )
        
        self.billing_admin_role = Role.objects.create(
            name='billing_admin',
            display_name='Billing Admin',
            service=self.billing_service
        )
        
        self.billing_viewer_role = Role.objects.create(
            name='billing_viewer',
            display_name='Billing Viewer',
            service=self.billing_service
        )
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        
        UserRole.objects.create(
            user=self.admin_user,
            role=self.admin_role,
            assigned_by=self.admin_user
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='regular123'
        )
        
        # Create test users
        self.test_user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='test123'
        )
        
        self.test_user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='test123'
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Cache admin user attributes
        RedisService.populate_user_attributes(self.admin_user.id, 'identity_provider')
    
    def authenticate_as_admin(self):
        """Authenticate client as admin"""
        token = generate_jwt_token(self.admin_user)
        self.client.cookies['jwt'] = token
    
    def authenticate_as_regular(self):
        """Authenticate client as regular user"""
        token = generate_jwt_token(self.regular_user)
        self.client.cookies['jwt'] = token


class UserListAPITest(AdminAPITestCase):
    """Test user list endpoint"""
    
    def test_list_users_requires_auth(self):
        """Test that listing users requires authentication"""
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_list_users_requires_admin(self):
        """Test that listing users requires admin role"""
        self.authenticate_as_regular()
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_list_users_success(self):
        """Test successful user listing"""
        self.authenticate_as_admin()
        response = self.client.get('/api/admin/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 4)  # admin + regular + test1 + test2
    
    def test_search_users(self):
        """Test user search functionality"""
        self.authenticate_as_admin()
        
        # Search by username
        response = self.client.get('/api/admin/users/?search=test')
        data = response.json()
        self.assertEqual(data['count'], 2)  # testuser1 and testuser2
        
        # Search by email
        response = self.client.get('/api/admin/users/?search=admin@')
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['username'], 'admin')
    
    def test_filter_by_active_status(self):
        """Test filtering by active status"""
        self.authenticate_as_admin()
        
        # Deactivate a user
        self.test_user1.is_active = False
        self.test_user1.save()
        
        # Filter active users
        response = self.client.get('/api/admin/users/?is_active=true')
        data = response.json()
        self.assertEqual(data['count'], 3)
        
        # Filter inactive users
        response = self.client.get('/api/admin/users/?is_active=false')
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['username'], 'testuser1')
    
    def test_filter_by_role(self):
        """Test filtering by role"""
        self.authenticate_as_admin()
        
        # Assign role to test user
        UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_admin_role,
            assigned_by=self.admin_user
        )
        
        response = self.client.get('/api/admin/users/?has_role=billing_admin')
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['username'], 'testuser1')
    
    def test_pagination(self):
        """Test pagination"""
        self.authenticate_as_admin()
        
        # Create more users
        for i in range(60):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='test123'
            )
        
        # Default page size is 50
        response = self.client.get('/api/admin/users/')
        data = response.json()
        self.assertEqual(len(data['results']), 50)
        self.assertIsNotNone(data['next'])
        
        # Custom page size
        response = self.client.get('/api/admin/users/?page_size=10')
        data = response.json()
        self.assertEqual(len(data['results']), 10)


class UserDetailAPITest(AdminAPITestCase):
    """Test user detail endpoints"""
    
    def test_get_user_detail(self):
        """Test getting user details"""
        self.authenticate_as_admin()
        
        response = self.client.get(f'/api/admin/users/{self.test_user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(data['username'], 'testuser1')
        self.assertEqual(data['email'], 'test1@example.com')
        self.assertIn('roles', data)
    
    def test_create_user(self):
        """Test creating a new user"""
        self.authenticate_as_admin()
        
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
            'is_active': True
        }
        
        response = self.client.post('/api/admin/users/', user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('newpass123'))
    
    def test_create_user_with_initial_roles(self):
        """Test creating user with initial roles"""
        self.authenticate_as_admin()
        
        user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'initial_roles': [
                {
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post('/api/admin/users/', user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify role was assigned
        user = User.objects.get(username='newuser')
        self.assertTrue(
            UserRole.objects.filter(
                user=user,
                role=self.billing_admin_role
            ).exists()
        )
    
    def test_create_duplicate_username(self):
        """Test creating user with duplicate username"""
        self.authenticate_as_admin()
        
        user_data = {
            'username': 'testuser1',  # Already exists
            'email': 'another@example.com',
            'password': 'test123'
        }
        
        response = self.client.post('/api/admin/users/', user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.json())
    
    def test_update_user(self):
        """Test updating user"""
        self.authenticate_as_admin()
        
        update_data = {
            'email': 'updated@example.com',
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(
            f'/api/admin/users/{self.test_user1.id}/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify changes
        self.test_user1.refresh_from_db()
        self.assertEqual(self.test_user1.email, 'updated@example.com')
        self.assertEqual(self.test_user1.first_name, 'Updated')
    
    def test_deactivate_user(self):
        """Test deactivating user (soft delete)"""
        self.authenticate_as_admin()
        
        response = self.client.delete(f'/api/admin/users/{self.test_user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify user is deactivated, not deleted
        self.test_user1.refresh_from_db()
        self.assertFalse(self.test_user1.is_active)
        self.assertTrue(User.objects.filter(id=self.test_user1.id).exists())
    
    def test_cannot_delete_superuser(self):
        """Test that superusers cannot be deleted"""
        self.authenticate_as_admin()
        
        # Make user a superuser
        self.test_user1.is_superuser = True
        self.test_user1.save()
        
        response = self.client.delete(f'/api/admin/users/{self.test_user1.id}/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_set_password(self):
        """Test setting user password"""
        self.authenticate_as_admin()
        
        password_data = {
            'password': 'newpassword123',
            'force_change': True
        }
        
        response = self.client.post(
            f'/api/admin/users/{self.test_user1.id}/set-password/',
            password_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.test_user1.refresh_from_db()
        self.assertTrue(self.test_user1.check_password('newpassword123'))


class RoleManagementAPITest(AdminAPITestCase):
    """Test role management endpoints"""
    
    def test_list_user_roles(self):
        """Test listing user's roles"""
        self.authenticate_as_admin()
        
        # Assign some roles
        UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_admin_role,
            assigned_by=self.admin_user
        )
        UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_viewer_role,
            assigned_by=self.admin_user,
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        response = self.client.get(f'/api/admin/users/{self.test_user1.id}/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['role_name'], 'billing_admin')
        self.assertTrue(data[0]['is_active'])
    
    def test_assign_role(self):
        """Test assigning role to user"""
        self.authenticate_as_admin()
        
        role_data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api',
            'reason': 'Test assignment'
        }
        
        response = self.client.post(
            f'/api/admin/users/{self.test_user1.id}/roles/',
            role_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify role was assigned
        self.assertTrue(
            UserRole.objects.filter(
                user=self.test_user1,
                role=self.billing_admin_role
            ).exists()
        )
    
    def test_assign_role_with_expiration(self):
        """Test assigning role with expiration date"""
        self.authenticate_as_admin()
        
        expires_at = timezone.now() + timedelta(days=90)
        role_data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api',
            'expires_at': expires_at.isoformat()
        }
        
        response = self.client.post(
            f'/api/admin/users/{self.test_user1.id}/roles/',
            role_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify expiration was set
        user_role = UserRole.objects.get(
            user=self.test_user1,
            role=self.billing_admin_role
        )
        self.assertIsNotNone(user_role.expires_at)
    
    def test_cannot_assign_duplicate_role(self):
        """Test that duplicate roles cannot be assigned"""
        self.authenticate_as_admin()
        
        # First assignment
        UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_admin_role,
            assigned_by=self.admin_user
        )
        
        # Try to assign again
        role_data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api'
        }
        
        response = self.client.post(
            f'/api/admin/users/{self.test_user1.id}/roles/',
            role_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_revoke_role(self):
        """Test revoking role from user"""
        self.authenticate_as_admin()
        
        # Assign role
        user_role = UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_admin_role,
            assigned_by=self.admin_user
        )
        
        response = self.client.delete(
            f'/api/admin/users/{self.test_user1.id}/roles/{user_role.id}/'
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify role was revoked
        self.assertFalse(
            UserRole.objects.filter(id=user_role.id).exists()
        )


class ServiceAndRoleAPITest(AdminAPITestCase):
    """Test service and role listing endpoints"""
    
    def test_list_services(self):
        """Test listing services"""
        self.authenticate_as_admin()
        
        response = self.client.get('/api/admin/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 2)  # identity_provider and billing_api
        
        # Check service details
        billing = next(s for s in data if s['name'] == 'billing_api')
        self.assertEqual(billing['display_name'], 'Billing API')
        self.assertEqual(billing['role_count'], 2)
    
    def test_list_roles(self):
        """Test listing roles"""
        self.authenticate_as_admin()
        
        response = self.client.get('/api/admin/roles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 3)  # identity_admin, billing_admin, billing_viewer
    
    def test_filter_roles_by_service(self):
        """Test filtering roles by service"""
        self.authenticate_as_admin()
        
        response = self.client.get('/api/admin/roles/?service=billing_api')
        data = response.json()
        self.assertEqual(len(data), 2)
        
        for role in data:
            self.assertEqual(role['service_name'], 'billing_api')
    
    def test_filter_global_roles(self):
        """Test filtering global roles"""
        self.authenticate_as_admin()
        
        response = self.client.get('/api/admin/roles/?is_global=true')
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'identity_admin')


class BulkOperationsAPITest(AdminAPITestCase):
    """Test bulk operations"""
    
    def test_bulk_assign_roles(self):
        """Test bulk role assignment"""
        self.authenticate_as_admin()
        
        bulk_data = {
            'assignments': [
                {
                    'user_id': self.test_user1.id,
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                },
                {
                    'user_id': self.test_user2.id,
                    'role_name': 'billing_viewer',
                    'service_name': 'billing_api'
                }
            ],
            'expires_at': (timezone.now() + timedelta(days=30)).isoformat()
        }
        
        response = self.client.post(
            '/api/admin/bulk/assign-roles/',
            bulk_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        self.assertEqual(data['success'], 2)
        self.assertEqual(len(data['created']), 2)
        
        # Verify roles were assigned
        self.assertTrue(
            UserRole.objects.filter(
                user=self.test_user1,
                role=self.billing_admin_role
            ).exists()
        )
        self.assertTrue(
            UserRole.objects.filter(
                user=self.test_user2,
                role=self.billing_viewer_role
            ).exists()
        )
    
    def test_bulk_assign_with_errors(self):
        """Test bulk assignment with some errors"""
        self.authenticate_as_admin()
        
        # Pre-assign a role
        UserRole.objects.create(
            user=self.test_user1,
            role=self.billing_admin_role,
            assigned_by=self.admin_user
        )
        
        bulk_data = {
            'assignments': [
                {
                    'user_id': self.test_user1.id,
                    'role_name': 'billing_admin',  # Already assigned
                    'service_name': 'billing_api'
                },
                {
                    'user_id': self.test_user2.id,
                    'role_name': 'billing_viewer',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post(
            '/api/admin/bulk/assign-roles/',
            bulk_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        data = response.json()
        self.assertEqual(data['success'], 1)
        self.assertEqual(len(data['errors']), 1)
        self.assertEqual(data['errors'][0]['error'], 'Role already assigned')
    
    def test_bulk_assign_validation(self):
        """Test bulk assignment validation"""
        self.authenticate_as_admin()
        
        # Invalid user ID
        bulk_data = {
            'assignments': [
                {
                    'user_id': 9999,  # Non-existent
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post(
            '/api/admin/bulk/assign-roles/',
            bulk_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CacheInvalidationTest(AdminAPITestCase):
    """Test that cache is properly invalidated"""
    
    def test_cache_cleared_on_role_assignment(self):
        """Test cache is cleared when role is assigned"""
        self.authenticate_as_admin()
        
        # Pre-cache user attributes
        RedisService.populate_user_attributes(self.test_user1.id, 'billing_api')
        
        # Assign role
        role_data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api'
        }
        
        response = self.client.post(
            f'/api/admin/users/{self.test_user1.id}/roles/',
            role_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify cache was cleared
        cached = self.redis_service.get_user_attributes(self.test_user1.id, 'billing_api')
        self.assertIsNone(cached)
    
    def test_cache_cleared_on_user_update(self):
        """Test cache is cleared when user is updated"""
        self.authenticate_as_admin()
        
        # Pre-cache user attributes
        RedisService.populate_user_attributes(self.test_user1.id, 'identity_provider')
        
        # Update user
        update_data = {'email': 'newemail@example.com'}
        response = self.client.patch(
            f'/api/admin/users/{self.test_user1.id}/',
            update_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cache was cleared
        cached = self.redis_service.get_user_attributes(self.test_user1.id, 'identity_provider')
        self.assertIsNone(cached)