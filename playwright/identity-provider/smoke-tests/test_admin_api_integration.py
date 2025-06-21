"""
Integration tests for Identity Provider Admin API
Tests complex workflows and cache invalidation
"""
import pytest
from urllib.parse import urljoin
import time
import requests


def test_user_lifecycle_with_roles(page, api_client, admin_auth_cookies):
    """Test complete user lifecycle: create, assign roles, update, deactivate"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    timestamp = int(time.time())
    
    # 1. Create user
    user_data = {
        'username': f'lifecycle_{timestamp}',
        'email': f'lifecycle_{timestamp}@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # 2. Get available roles
    response = api_client.get('api/admin/roles/')
    roles = [r for r in response['json'] if r['name'] != 'identity_admin']
    
    if len(roles) < 2:
        pytest.skip("Not enough roles for lifecycle test")
    
    # 3. Assign first role
    role_data = {
        'role_name': roles[0]['name'],
        'service_name': roles[0]['service_name'],
        'reason': 'Initial assignment'
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 201
    first_role_id = response['json']['id']
    
    # 4. Verify user has role
    response = api_client.get(f'api/admin/users/{user_id}/')
    user = response['json']
    assert len(user['roles']) == 1
    assert user['roles'][0]['role_name'] == roles[0]['name']
    
    # 5. Update user details
    update_data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'email': f'updated_{timestamp}@example.com'
    }
    
    response = api_client.patch(f'api/admin/users/{user_id}/', update_data)
    assert response['status'] == 200
    
    # 6. Assign second role
    role_data = {
        'role_name': roles[1]['name'],
        'service_name': roles[1]['service_name']
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 201
    
    # 7. List user roles
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    user_roles = response['json']
    assert len(user_roles) == 2
    
    # 8. Revoke first role
    response = api_client.delete(f'api/admin/users/{user_id}/roles/{first_role_id}/')
    assert response['status'] == 204
    
    # 9. Verify role was revoked
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    user_roles = response['json']
    assert len(user_roles) == 1
    assert user_roles[0]['role_name'] == roles[1]['name']
    
    # 10. Deactivate user
    response = api_client.delete(f'api/admin/users/{user_id}/')
    assert response['status'] == 204
    
    # 11. Verify user is deactivated
    response = api_client.get(f'api/admin/users/{user_id}/')
    assert response['status'] == 200
    assert response['json']['is_active'] == False


def test_search_and_filter_workflow(page, api_client, admin_auth_cookies):
    """Test search and filter capabilities"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    timestamp = int(time.time())
    
    # Create test users with specific patterns
    created_users = []
    
    # Create active users
    for i in range(3):
        user_data = {
            'username': f'search_active_{i}_{timestamp}',
            'email': f'active_{i}_{timestamp}@test.com',
            'password': 'TestPass123!',
            'is_active': True
        }
        response = api_client.post('api/admin/users/', user_data)
        assert response['status'] == 201
        created_users.append(response['json']['id'])
    
    # Create inactive user
    user_data = {
        'username': f'search_inactive_{timestamp}',
        'email': f'inactive_{timestamp}@test.com',
        'password': 'TestPass123!',
        'is_active': False
    }
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    inactive_user_id = response['json']['id']
    
    # Get a role to assign
    response = api_client.get('api/admin/roles/')
    test_role = next((r for r in response['json'] if r['name'] != 'identity_admin'), None)
    
    if test_role:
        # Assign role to first two users
        for user_id in created_users[:2]:
            role_data = {
                'role_name': test_role['name'],
                'service_name': test_role['service_name']
            }
            response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
            assert response['status'] == 201
    
    # Test search by username pattern
    response = api_client.get(f'api/admin/users/?search=search_active_{timestamp}')
    results = response['json']
    assert results['count'] >= 3
    
    # Test search by email pattern
    response = api_client.get(f'api/admin/users/?search={timestamp}@test.com')
    results = response['json']
    assert results['count'] >= 4
    
    # Test filter by active status
    response = api_client.get('api/admin/users/?is_active=false')
    results = response['json']
    inactive_users = [u for u in results['results'] if u['id'] == inactive_user_id]
    assert len(inactive_users) == 1
    
    # Test filter by role (if role was assigned)
    if test_role:
        response = api_client.get(f'api/admin/users/?has_role={test_role["name"]}')
        results = response['json']
        # Should find at least the 2 users we assigned the role to
        user_ids = [u['id'] for u in results['results']]
        assert created_users[0] in user_ids
        assert created_users[1] in user_ids


def test_concurrent_role_operations(page, api_client, admin_auth_cookies):
    """Test handling of concurrent role operations"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    timestamp = int(time.time())
    
    # Create a user
    user_data = {
        'username': f'concurrent_{timestamp}',
        'email': f'concurrent_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get multiple roles
    response = api_client.get('api/admin/roles/')
    available_roles = [r for r in response['json'] if r['name'] != 'identity_admin']
    
    if len(available_roles) < 3:
        pytest.skip("Not enough roles for concurrent test")
    
    # Assign multiple roles in sequence
    assigned_roles = []
    for i in range(3):
        role_data = {
            'role_name': available_roles[i]['name'],
            'service_name': available_roles[i]['service_name']
        }
        response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
        assert response['status'] == 201
        assigned_roles.append(response['json']['id'])
    
    # Verify all roles are assigned
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    user_roles = response['json']
    assert len(user_roles) == 3
    
    # Revoke middle role
    response = api_client.delete(f'api/admin/users/{user_id}/roles/{assigned_roles[1]}/')
    assert response['status'] == 204
    
    # Verify correct roles remain
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    user_roles = response['json']
    assert len(user_roles) == 2
    
    remaining_role_ids = [r['id'] for r in user_roles]
    assert assigned_roles[0] in remaining_role_ids
    assert assigned_roles[2] in remaining_role_ids
    assert assigned_roles[1] not in remaining_role_ids


def test_cache_invalidation_on_updates(page, api_client, admin_auth_cookies):
    """Test that cache is properly invalidated on updates"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    timestamp = int(time.time())
    
    # Create a user
    user_data = {
        'username': f'cachetest_{timestamp}',
        'email': f'cache_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get user profile (this might cache data)
    response = api_client.get(f'api/admin/users/{user_id}/')
    original_email = response['json']['email']
    
    # Update user email
    update_data = {
        'email': f'updated_cache_{timestamp}@example.com'
    }
    response = api_client.patch(f'api/admin/users/{user_id}/', update_data)
    assert response['status'] == 200
    
    # Get user again - should see updated email
    response = api_client.get(f'api/admin/users/{user_id}/')
    assert response['json']['email'] == update_data['email']
    assert response['json']['email'] != original_email
    
    # Assign a role
    response = api_client.get('api/admin/roles/')
    test_role = next((r for r in response['json'] if r['name'] != 'identity_admin'), None)
    
    if test_role:
        role_data = {
            'role_name': test_role['name'],
            'service_name': test_role['service_name']
        }
        response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
        assert response['status'] == 201
        
        # User should immediately show the new role
        response = api_client.get(f'api/admin/users/{user_id}/')
        user_roles = response['json']['roles']
        assert len(user_roles) == 1
        assert user_roles[0]['role_name'] == test_role['name']


def test_error_handling_and_recovery(page, api_client, admin_auth_cookies):
    """Test API error handling and recovery"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Test invalid user ID
    response = api_client.get('api/admin/users/99999/')
    assert response['status'] == 404
    
    # Test invalid role assignment
    response = api_client.post('api/admin/users/99999/roles/', {
        'role_name': 'fake_role',
        'service_name': 'fake_service'
    })
    assert response['status'] in [400, 404]
    
    # Test malformed data
    response = api_client.post('api/admin/users/', {
        'username': '',  # Empty username
        'password': '123'  # Too short
    })
    assert response['status'] == 400
    assert 'username' in response['json'] or 'password' in response['json']
    
    # API should still be functional after errors
    response = api_client.get('api/admin/users/')
    assert response['status'] == 200
    
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    response = api_client.get('api/admin/services/')
    assert response['status'] == 200