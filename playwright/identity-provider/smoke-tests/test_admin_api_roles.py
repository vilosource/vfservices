"""
Playwright tests for Identity Provider Admin API - Role Management
"""
import pytest
from urllib.parse import urljoin
import time


def test_list_user_roles(page, api_client, admin_auth_cookies):
    """Test listing user's roles"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # First get a user with roles
    response = api_client.get('api/admin/users/?has_role=identity_admin')
    assert response['status'] == 200
    
    users_with_roles = response['json']['results']
    if not users_with_roles:
        pytest.skip("No users with roles found")
    
    user_id = users_with_roles[0]['id']
    
    # List user roles
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    
    assert response['status'] == 200
    roles = response['json']
    assert isinstance(roles, list)
    assert len(roles) > 0
    
    # Verify role structure
    role = roles[0]
    assert 'id' in role
    assert 'role_name' in role
    assert 'service_name' in role
    assert 'display_name' in role
    assert 'assigned_at' in role
    assert 'assigned_by' in role
    assert 'expires_at' in role
    assert 'is_active' in role


def test_assign_role_to_user(page, api_client, admin_auth_cookies):
    """Test assigning role to user"""
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
        'username': f'roletest_{timestamp}',
        'email': f'roletest_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get available roles
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    roles = response['json']
    
    # Find a role to assign (not identity_admin)
    test_role = None
    for role in roles:
        if role['name'] != 'identity_admin':
            test_role = role
            break
    
    if not test_role:
        pytest.skip("No suitable roles available for testing")
    
    # Assign role
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name'],
        'reason': 'Test assignment'
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    
    assert response['status'] == 201
    assigned_role = response['json']
    
    # Verify assignment
    assert assigned_role['role_name'] == test_role['name']
    assert assigned_role['service_name'] == test_role['service_name']
    assert assigned_role['is_active'] == True
    assert 'id' in assigned_role


def test_assign_role_with_expiration(page, api_client, admin_auth_cookies):
    """Test assigning role with expiration date"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create a user
    timestamp = int(time.time())
    user_data = {
        'username': f'expiretest_{timestamp}',
        'email': f'expire_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get a role
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    test_role = next((r for r in roles if r['name'] != 'identity_admin'), None)
    
    if not test_role:
        pytest.skip("No suitable roles available")
    
    # Assign role with expiration (30 days from now)
    from datetime import datetime, timedelta
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat() + 'Z'
    
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name'],
        'expires_at': expires_at
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    
    assert response['status'] == 201
    assigned_role = response['json']
    
    # Verify expiration is set
    assert assigned_role['expires_at'] is not None
    assert expires_at[:10] in assigned_role['expires_at']  # Check date part


def test_cannot_assign_duplicate_role(page, api_client, admin_auth_cookies):
    """Test that duplicate roles cannot be assigned"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create a user
    timestamp = int(time.time())
    user_data = {
        'username': f'duptest_{timestamp}',
        'email': f'dup_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get a role
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    test_role = next((r for r in roles if r['name'] != 'identity_admin'), None)
    
    if not test_role:
        pytest.skip("No suitable roles available")
    
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name']
    }
    
    # First assignment should succeed
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 201
    
    # Second assignment should fail
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 400
    assert 'already assigned' in str(response['json']).lower()


def test_revoke_role_from_user(page, api_client, admin_auth_cookies):
    """Test revoking role from user"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create a user with a role
    timestamp = int(time.time())
    user_data = {
        'username': f'revoketest_{timestamp}',
        'email': f'revoke_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Get a role and assign it
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    test_role = next((r for r in roles if r['name'] != 'identity_admin'), None)
    
    if not test_role:
        pytest.skip("No suitable roles available")
    
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name']
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 201
    role_assignment_id = response['json']['id']
    
    # Revoke the role
    response = api_client.delete(f'api/admin/users/{user_id}/roles/{role_assignment_id}/')
    
    assert response['status'] == 204
    
    # Verify role is gone
    response = api_client.get(f'api/admin/users/{user_id}/roles/')
    assert response['status'] == 200
    remaining_roles = response['json']
    
    # Should not find the revoked role
    for role in remaining_roles:
        assert role['id'] != role_assignment_id


def test_list_all_services(page, api_client, admin_auth_cookies):
    """Test listing all services"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    response = api_client.get('api/admin/services/')
    
    assert response['status'] == 200
    services = response['json']
    assert isinstance(services, list)
    assert len(services) > 0
    
    # Verify service structure
    service = services[0]
    assert 'id' in service
    assert 'name' in service
    assert 'display_name' in service
    assert 'description' in service
    assert 'version' in service
    assert 'role_count' in service
    assert 'is_active' in service


def test_list_all_roles(page, api_client, admin_auth_cookies):
    """Test listing all roles"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    response = api_client.get('api/admin/roles/')
    
    assert response['status'] == 200
    roles = response['json']
    assert isinstance(roles, list)
    assert len(roles) > 0
    
    # Verify role structure
    role = roles[0]
    assert 'id' in role
    assert 'name' in role
    assert 'display_name' in role
    assert 'description' in role
    assert 'service_name' in role
    assert 'service_display_name' in role
    assert 'is_global' in role
    assert 'user_count' in role
    
    # Verify identity_admin role exists
    admin_role = next((r for r in roles if r['name'] == 'identity_admin'), None)
    assert admin_role is not None
    assert admin_role['is_global'] == True


def test_filter_roles_by_service(page, api_client, admin_auth_cookies):
    """Test filtering roles by service"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Get services first
    response = api_client.get('api/admin/services/')
    services = response['json']
    
    if len(services) < 2:
        pytest.skip("Need at least 2 services for filtering test")
    
    # Filter by first service
    service_name = services[0]['name']
    response = api_client.get(f'api/admin/roles/?service={service_name}')
    
    assert response['status'] == 200
    filtered_roles = response['json']
    
    # All roles should belong to the filtered service
    for role in filtered_roles:
        assert role['service_name'] == service_name


def test_filter_global_roles(page, api_client, admin_auth_cookies):
    """Test filtering global roles"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    response = api_client.get('api/admin/roles/?is_global=true')
    
    assert response['status'] == 200
    global_roles = response['json']
    
    # All roles should be global
    for role in global_roles:
        assert role['is_global'] == True
    
    # identity_admin should be in the list
    admin_role = next((r for r in global_roles if r['name'] == 'identity_admin'), None)
    assert admin_role is not None