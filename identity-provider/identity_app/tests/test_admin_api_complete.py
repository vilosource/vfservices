"""
Comprehensive tests for Identity Provider Admin API endpoints.
Tests all admin ViewSet actions and bulk operations.
"""
import json
from datetime import timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock

from ..models import Service, Role, UserRole, ServiceManifest
from ..services import RedisService


class AdminAPICompleteTestCase(TestCase):
    """Comprehensive test cases for admin API endpoints."""
    
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
        
        self.billing_viewer_role = Role.objects.create(
            name='billing_viewer',
            display_name='Billing Viewer',
            service=self.billing_service,
            is_global=False
        )
        
        # Authenticate as admin for most tests
        self._authenticate_as_admin()
    
    def _authenticate_as_admin(self):
        """Helper to authenticate as admin user."""
        self.client.force_authenticate(user=self.admin_user)
    
    def _authenticate_as_user(self):
        """Helper to authenticate as regular user."""
        self.client.force_authenticate(user=self.test_user)


class UserViewSetTestCase(AdminAPICompleteTestCase):
    """Test cases for UserViewSet endpoints."""
    
    def test_list_users(self):
        """Test listing users."""
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('results', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 2)  # admin and test user
        
        # Check user data structure
        user_data = data['results'][0]
        self.assertIn('id', user_data)
        self.assertIn('username', user_data)
        self.assertIn('email', user_data)
        self.assertIn('is_active', user_data)
        self.assertIn('roles_count', user_data)
    
    def test_list_users_with_search(self):
        """Test listing users with search filter."""
        url = reverse('admin-user-list')
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['username'], 'testuser')
    
    def test_list_users_with_filters(self):
        """Test listing users with various filters."""
        # Filter by active status
        url = reverse('admin-user-list')
        response = self.client.get(url, {'is_active': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 2)
        
        # Filter by role
        response = self.client.get(url, {'has_role': 'identity_admin'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['results'][0]['username'], 'admin')
    
    def test_list_users_pagination(self):
        """Test user list pagination."""
        # Create more users
        for i in range(60):
            User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='password123!#QWERT'
            )
        
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data['results']), 50)  # Default page size
        self.assertIsNotNone(data['next'])
        
        # Test custom page size
        response = self.client.get(url, {'page_size': 10})
        data = response.json()
        self.assertEqual(len(data['results']), 10)
    
    def test_get_user_detail(self):
        """Test getting user details."""
        url = reverse('admin-user-detail', kwargs={'pk': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['id'], self.test_user.id)
        self.assertEqual(data['username'], 'testuser')
        self.assertIn('roles', data)
        self.assertIn('groups', data)
        self.assertIn('user_permissions', data)
    
    def test_create_user(self):
        """Test creating a new user."""
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
                    'role_name': 'billing_viewer',
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
        
        # Verify role was assigned
        user_roles = UserRole.objects.filter(user=user)
        self.assertEqual(user_roles.count(), 1)
        self.assertEqual(user_roles.first().role.name, 'billing_viewer')
    
    def test_update_user(self):
        """Test updating user information."""
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
        self.assertEqual(self.test_user.first_name, 'Updated')
    
    def test_deactivate_user(self):
        """Test deactivating a user."""
        url = reverse('admin-user-detail', kwargs={'pk': self.test_user.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify user was deactivated
        self.test_user.refresh_from_db()
        self.assertFalse(self.test_user.is_active)
    
    def test_cannot_delete_superuser(self):
        """Test that superuser accounts cannot be deleted."""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='super123!#QWERT'
        )
        
        url = reverse('admin-user-detail', kwargs={'pk': superuser.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('superuser', data['error'])
    
    def test_set_password(self):
        """Test setting user password."""
        url = reverse('admin-user-set-password', kwargs={'pk': self.test_user.id})
        data = {
            'password': 'newpassword123!#QWERT'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify password was changed
        self.test_user.refresh_from_db()
        self.assertTrue(self.test_user.check_password('newpassword123!#QWERT'))
    
    def test_list_user_roles(self):
        """Test listing user's roles."""
        # Assign a role to test user
        UserRole.objects.create(
            user=self.test_user,
            role=self.billing_viewer_role,
            granted_by=self.admin_user
        )
        
        url = reverse('admin-user-roles', kwargs={'pk': self.test_user.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['role']['name'], 'billing_viewer')
        self.assertIn('granted_at', data[0])
        self.assertIn('granted_by', data[0])
    
    def test_assign_role_to_user(self):
        """Test assigning a role to a user."""
        url = reverse('admin-user-roles', kwargs={'pk': self.test_user.id})
        data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api',
            'expires_at': (timezone.now() + timedelta(days=30)).isoformat(),
            'reason': 'Temporary access for project'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify role was assigned
        user_role = UserRole.objects.get(
            user=self.test_user,
            role__name='billing_admin'
        )
        self.assertIsNotNone(user_role.expires_at)
    
    def test_cannot_assign_duplicate_role(self):
        """Test that duplicate roles cannot be assigned."""
        # First assignment
        UserRole.objects.create(
            user=self.test_user,
            role=self.billing_admin_role,
            granted_by=self.admin_user
        )
        
        # Try to assign again
        url = reverse('admin-user-roles', kwargs={'pk': self.test_user.id})
        data = {
            'role_name': 'billing_admin',
            'service_name': 'billing_api'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('error', data)
        self.assertIn('already assigned', data['error'])
    
    def test_revoke_role_from_user(self):
        """Test revoking a role from a user."""
        # Assign role first
        user_role = UserRole.objects.create(
            user=self.test_user,
            role=self.billing_admin_role,
            granted_by=self.admin_user
        )
        
        url = reverse('admin-user-revoke-role', kwargs={
            'pk': self.test_user.id,
            'role_id': user_role.id
        })
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify role was revoked
        self.assertFalse(
            UserRole.objects.filter(id=user_role.id).exists()
        )
    
    def test_requires_admin_permission(self):
        """Test that admin endpoints require identity_admin role."""
        # Authenticate as regular user
        self._authenticate_as_user()
        
        url = reverse('admin-user-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ServiceViewSetTestCase(AdminAPICompleteTestCase):
    """Test cases for ServiceViewSet endpoints."""
    
    def test_list_services(self):
        """Test listing services."""
        url = reverse('admin-service-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 2)  # identity_provider and billing_api
        
        # Check service data structure
        service_data = next(s for s in data if s['name'] == 'billing_api')
        self.assertEqual(service_data['display_name'], 'Billing API')
        self.assertIn('description', service_data)
        self.assertIn('is_active', service_data)
        self.assertIn('created_at', service_data)
    
    def test_get_service_detail(self):
        """Test getting service details."""
        url = reverse('admin-service-detail', kwargs={'pk': self.billing_service.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['name'], 'billing_api')
        self.assertEqual(data['display_name'], 'Billing API')


class RoleViewSetTestCase(AdminAPICompleteTestCase):
    """Test cases for RoleViewSet endpoints."""
    
    def test_list_roles(self):
        """Test listing roles."""
        url = reverse('admin-role-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(len(data), 3)  # identity_admin, billing_admin, billing_viewer
        
        # Check role data structure
        role_data = data[0]
        self.assertIn('id', role_data)
        self.assertIn('name', role_data)
        self.assertIn('display_name', role_data)
        self.assertIn('service', role_data)
        self.assertIn('is_global', role_data)
    
    def test_list_roles_with_filters(self):
        """Test listing roles with filters."""
        url = reverse('admin-role-list')
        
        # Filter by service
        response = self.client.get(url, {'service': 'billing_api'})
        data = response.json()
        
        self.assertEqual(len(data), 2)
        for role in data:
            self.assertEqual(role['service']['name'], 'billing_api')
        
        # Filter by is_global
        response = self.client.get(url, {'is_global': 'true'})
        data = response.json()
        
        for role in data:
            self.assertTrue(role['is_global'])
    
    def test_get_role_detail(self):
        """Test getting role details."""
        url = reverse('admin-role-detail', kwargs={'pk': self.billing_admin_role.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertEqual(data['name'], 'billing_admin')
        self.assertEqual(data['service']['name'], 'billing_api')


class BulkOperationsTestCase(AdminAPICompleteTestCase):
    """Test cases for bulk operations."""
    
    def test_bulk_assign_roles_success(self):
        """Test successful bulk role assignment."""
        # Create additional users
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
                    'role_name': 'billing_viewer',
                    'service_name': 'billing_api'
                },
                {
                    'username': 'user2',
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ],
            'expires_at': (timezone.now() + timedelta(days=90)).isoformat(),
            'reason': 'Bulk assignment for new team'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['total'], 2)
        self.assertEqual(response_data['success'], 2)
        self.assertEqual(len(response_data['created']), 2)
        self.assertEqual(len(response_data['errors']), 0)
        
        # Verify assignments
        self.assertTrue(
            UserRole.objects.filter(
                user__username='testuser',
                role__name='billing_viewer'
            ).exists()
        )
    
    def test_bulk_assign_roles_partial_success(self):
        """Test bulk assignment with some failures."""
        url = reverse('admin-bulk-assign-roles')
        data = {
            'assignments': [
                {
                    'username': 'testuser',
                    'role_name': 'billing_viewer',
                    'service_name': 'billing_api'
                },
                {
                    'username': 'nonexistent',
                    'role_name': 'billing_admin',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_data = response.json()
        
        self.assertEqual(response_data['total'], 2)
        self.assertEqual(response_data['success'], 1)
        self.assertEqual(len(response_data['created']), 1)
        self.assertEqual(len(response_data['errors']), 1)
        
        # Check error details
        error = response_data['errors'][0]
        self.assertEqual(error['user'], 'nonexistent')
        self.assertIn('not found', error['error'])
    
    def test_bulk_assign_duplicate_roles(self):
        """Test bulk assignment handles duplicate role assignments."""
        # Pre-assign a role
        UserRole.objects.create(
            user=self.test_user,
            role=self.billing_viewer_role,
            granted_by=self.admin_user
        )
        
        url = reverse('admin-bulk-assign-roles')
        data = {
            'assignments': [
                {
                    'username': 'testuser',
                    'role_name': 'billing_viewer',
                    'service_name': 'billing_api'
                }
            ]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        
        self.assertEqual(len(response_data['errors']), 1)
        self.assertIn('already assigned', response_data['errors'][0]['error'])


class AuditLogTestCase(AdminAPICompleteTestCase):
    """Test cases for audit log endpoint."""
    
    def test_audit_log_endpoint(self):
        """Test audit log endpoint (currently returns empty)."""
        url = reverse('admin-audit-log')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        # Currently returns empty results
        self.assertEqual(data['results'], [])
        self.assertEqual(data['count'], 0)


class AdminAPIPermissionsTestCase(AdminAPICompleteTestCase):
    """Test cases for admin API permissions."""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        self.client.force_authenticate(user=None)
        
        urls = [
            reverse('admin-user-list'),
            reverse('admin-service-list'),
            reverse('admin-role-list'),
            reverse('admin-bulk-assign-roles'),
            reverse('admin-audit-log')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                f"Expected 403 for {url}"
            )
    
    def test_non_admin_access_denied(self):
        """Test that non-admin users are denied access."""
        self._authenticate_as_user()
        
        urls = [
            reverse('admin-user-list'),
            reverse('admin-service-list'),
            reverse('admin-role-list')
        ]
        
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code,
                status.HTTP_403_FORBIDDEN,
                f"Expected 403 for {url}"
            )
    
    @patch('identity_app.services.RedisService.invalidate_user_cache')
    def test_cache_invalidation_on_changes(self, mock_invalidate):
        """Test that cache is invalidated on user changes."""
        # Update user
        url = reverse('admin-user-detail', kwargs={'pk': self.test_user.id})
        data = {'email': 'newemail@example.com'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_invalidate.assert_called_with(self.test_user.id)
        
        # Assign role
        mock_invalidate.reset_mock()
        url = reverse('admin-user-roles', kwargs={'pk': self.test_user.id})
        data = {
            'role_name': 'billing_viewer',
            'service_name': 'billing_api'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_invalidate.assert_called_with(self.test_user.id)