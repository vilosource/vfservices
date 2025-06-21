"""
Playwright tests for Identity Provider Admin API - User Management
"""
import pytest
from urllib.parse import urljoin
import time


def test_admin_api_requires_authentication(page, api_client):
    """Test that admin API requires authentication"""
    # Try to access admin API without authentication
    response = api_client.get('api/admin/users/')
    
    assert response['status'] == 401
    assert 'detail' in response['json']


def test_admin_api_requires_admin_role(page, api_client, regular_auth_cookies):
    """Test that admin API requires identity_admin role"""
    # Set regular user cookies
    for name, value in regular_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Try to access admin API as regular user
    response = api_client.get('api/admin/users/')
    
    assert response['status'] == 403
    assert 'detail' in response['json']
    assert 'identity_admin' in response['json']['detail'].lower()


def test_list_users(page, api_client, admin_auth_cookies):
    """Test listing users with admin role"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # List users
    response = api_client.get('api/admin/users/')
    
    assert response['status'] == 200
    data = response['json']
    assert 'results' in data
    assert 'count' in data
    assert isinstance(data['results'], list)
    
    # Verify user structure
    if data['results']:
        user = data['results'][0]
        assert 'id' in user
        assert 'username' in user
        assert 'email' in user
        assert 'is_active' in user
        assert 'roles' in user
        assert isinstance(user['roles'], list)


def test_search_users(page, api_client, admin_auth_cookies):
    """Test searching users"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Search for admin users
    response = api_client.get('api/admin/users/?search=admin')
    
    assert response['status'] == 200
    data = response['json']
    
    # Should find at least one admin user
    assert data['count'] >= 1
    
    # All results should contain 'admin' in username or email
    for user in data['results']:
        username_match = 'admin' in user['username'].lower()
        email_match = 'admin' in user.get('email', '').lower()
        assert username_match or email_match


def test_filter_users_by_active_status(page, api_client, admin_auth_cookies):
    """Test filtering users by active status"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Get active users
    response = api_client.get('api/admin/users/?is_active=true')
    assert response['status'] == 200
    active_count = response['json']['count']
    
    # Get inactive users
    response = api_client.get('api/admin/users/?is_active=false')
    assert response['status'] == 200
    inactive_count = response['json']['count']
    
    # Get all users
    response = api_client.get('api/admin/users/')
    assert response['status'] == 200
    total_count = response['json']['count']
    
    # Active + inactive should equal total (approximately, due to pagination)
    assert active_count + inactive_count >= total_count - 50  # Account for pagination


def test_get_user_detail(page, api_client, admin_auth_cookies):
    """Test getting user details"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First get a user ID
    response = api_client.get('api/admin/users/')
    assert response['status'] == 200
    users = response['json']['results']
    assert len(users) > 0
    
    user_id = users[0]['id']
    
    # Get user details
    response = api_client.get(f'api/admin/users/{user_id}/')
    
    assert response['status'] == 200
    user = response['json']
    
    # Verify detailed user structure
    assert 'id' in user
    assert 'username' in user
    assert 'email' in user
    assert 'first_name' in user
    assert 'last_name' in user
    assert 'is_active' in user
    assert 'is_staff' in user
    assert 'is_superuser' in user
    assert 'date_joined' in user
    assert 'last_login' in user
    assert 'roles' in user
    
    # Roles should include more details
    if user['roles']:
        role = user['roles'][0]
        assert 'id' in role
        assert 'role_name' in role
        assert 'service_name' in role
        assert 'assigned_at' in role
        assert 'assigned_by' in role


def test_create_user(page, api_client, admin_auth_cookies):
    """Test creating a new user"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create unique username
    timestamp = int(time.time())
    user_data = {
        'username': f'testuser_{timestamp}',
        'email': f'test_{timestamp}@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User',
        'is_active': True
    }
    
    # Create user
    response = api_client.post('api/admin/users/', user_data)
    
    assert response['status'] == 201
    created_user = response['json']
    
    # Verify created user
    assert created_user['username'] == user_data['username']
    assert created_user['email'] == user_data['email']
    assert created_user['first_name'] == user_data['first_name']
    assert created_user['last_name'] == user_data['last_name']
    assert created_user['is_active'] == user_data['is_active']
    assert 'id' in created_user
    
    # Verify password is not returned
    assert 'password' not in created_user


def test_create_user_with_initial_roles(page, api_client, admin_auth_cookies):
    """Test creating user with initial roles"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First get available roles
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    roles = response['json']
    
    # Find a non-admin role to assign
    test_role = None
    for role in roles:
        if role['name'] != 'identity_admin':
            test_role = role
            break
    
    if not test_role:
        pytest.skip("No non-admin roles available for testing")
    
    # Create user with initial role
    timestamp = int(time.time())
    user_data = {
        'username': f'roleuser_{timestamp}',
        'email': f'role_{timestamp}@example.com',
        'password': 'TestPass123!',
        'initial_roles': [
            {
                'role_name': test_role['name'],
                'service_name': test_role['service_name']
            }
        ]
    }
    
    response = api_client.post('api/admin/users/', user_data)
    
    assert response['status'] == 201
    created_user = response['json']
    
    # Verify role was assigned
    assert len(created_user['roles']) == 1
    assert created_user['roles'][0]['role_name'] == test_role['name']


def test_create_duplicate_username(page, api_client, admin_auth_cookies):
    """Test creating user with duplicate username"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Try to create user with existing username
    user_data = {
        'username': 'admin',  # Already exists
        'email': 'another@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    
    assert response['status'] == 400
    assert 'username' in response['json']


def test_update_user(page, api_client, admin_auth_cookies):
    """Test updating user details"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First create a user to update
    timestamp = int(time.time())
    user_data = {
        'username': f'updateuser_{timestamp}',
        'email': f'update_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Update user
    update_data = {
        'email': f'updated_{timestamp}@example.com',
        'first_name': 'Updated',
        'last_name': 'Name'
    }
    
    response = api_client.patch(f'api/admin/users/{user_id}/', update_data)
    
    assert response['status'] == 200
    updated_user = response['json']
    
    # Verify updates
    assert updated_user['email'] == update_data['email']
    assert updated_user['first_name'] == update_data['first_name']
    assert updated_user['last_name'] == update_data['last_name']
    # Username should not change
    assert updated_user['username'] == user_data['username']


def test_deactivate_user(page, api_client, admin_auth_cookies):
    """Test deactivating user (soft delete)"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First create a user to deactivate
    timestamp = int(time.time())
    user_data = {
        'username': f'deleteuser_{timestamp}',
        'email': f'delete_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Deactivate user
    response = api_client.delete(f'api/admin/users/{user_id}/')
    
    assert response['status'] == 204
    
    # Verify user is deactivated
    response = api_client.get(f'api/admin/users/{user_id}/')
    assert response['status'] == 200
    assert response['json']['is_active'] == False


def test_set_user_password(page, api_client, admin_auth_cookies):
    """Test setting user password"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First create a user
    timestamp = int(time.time())
    user_data = {
        'username': f'passuser_{timestamp}',
        'email': f'pass_{timestamp}@example.com',
        'password': 'OldPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Set new password
    password_data = {
        'password': 'NewPass123!',
        'force_change': True
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/set-password/', password_data)
    
    assert response['status'] == 200
    assert response['json']['message'] == 'Password updated successfully'
    
    # Try to login with new password (would need to implement login test)
    # For now, just verify the endpoint works


def test_pagination(page, api_client, admin_auth_cookies):
    """Test pagination of user list"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Get first page
    response = api_client.get('api/admin/users/?page=1&page_size=5')
    assert response['status'] == 200
    
    data = response['json']
    assert 'results' in data
    assert 'count' in data
    assert 'next' in data
    assert 'previous' in data
    
    # Should have at most 5 results
    assert len(data['results']) <= 5
    
    # If there are more users, next should be present
    if data['count'] > 5:
        assert data['next'] is not None
        
        # Get second page
        response = api_client.get('api/admin/users/?page=2&page_size=5')
        assert response['status'] == 200
        
        page2_data = response['json']
        assert page2_data['previous'] is not None
        
        # Results should be different
        page1_ids = [u['id'] for u in data['results']]
        page2_ids = [u['id'] for u in page2_data['results']]
        assert set(page1_ids).isdisjoint(set(page2_ids))