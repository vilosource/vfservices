"""
Playwright tests for Identity Provider Admin API - Bulk Operations
"""
import pytest
from urllib.parse import urljoin
import time
from datetime import datetime, timedelta


def test_bulk_assign_roles(page, api_client, admin_auth_cookies):
    """Test bulk role assignment"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create test users
    timestamp = int(time.time())
    user_ids = []
    
    for i in range(3):
        user_data = {
            'username': f'bulkuser{i}_{timestamp}',
            'email': f'bulk{i}_{timestamp}@example.com',
            'password': 'TestPass123!'
        }
        response = api_client.post('api/admin/users/', user_data)
        assert response['status'] == 201
        user_ids.append(response['json']['id'])
    
    # Get available roles
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    
    # Find suitable roles
    available_roles = [r for r in roles if r['name'] != 'identity_admin']
    if len(available_roles) < 2:
        pytest.skip("Not enough roles for bulk assignment test")
    
    # Prepare bulk assignment data
    bulk_data = {
        'assignments': [
            {
                'user_id': user_ids[0],
                'role_name': available_roles[0]['name'],
                'service_name': available_roles[0]['service_name']
            },
            {
                'user_id': user_ids[1],
                'role_name': available_roles[0]['name'],
                'service_name': available_roles[0]['service_name']
            },
            {
                'user_id': user_ids[2],
                'role_name': available_roles[1]['name'],
                'service_name': available_roles[1]['service_name']
            }
        ]
    }
    
    # Perform bulk assignment
    response = api_client.post('api/admin/bulk/assign-roles/', bulk_data)
    
    assert response['status'] == 201
    result = response['json']
    
    # Verify results
    assert result['success'] == 3
    assert result['failed'] == 0
    assert len(result['created']) == 3
    assert len(result['errors']) == 0
    
    # Verify each assignment
    for created in result['created']:
        assert 'user_id' in created
        assert 'role_id' in created
        assert 'assignment_id' in created
        assert created['user_id'] in user_ids


def test_bulk_assign_with_expiration(page, api_client, admin_auth_cookies):
    """Test bulk assignment with expiration date"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create test users
    timestamp = int(time.time())
    user_ids = []
    
    for i in range(2):
        user_data = {
            'username': f'expireuser{i}_{timestamp}',
            'email': f'expire{i}_{timestamp}@example.com',
            'password': 'TestPass123!'
        }
        response = api_client.post('api/admin/users/', user_data)
        assert response['status'] == 201
        user_ids.append(response['json']['id'])
    
    # Get a role
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    test_role = next((r for r in roles if r['name'] != 'identity_admin'), None)
    
    if not test_role:
        pytest.skip("No suitable roles available")
    
    # Set expiration date
    expires_at = (datetime.utcnow() + timedelta(days=90)).isoformat() + 'Z'
    
    bulk_data = {
        'assignments': [
            {
                'user_id': user_ids[0],
                'role_name': test_role['name'],
                'service_name': test_role['service_name']
            },
            {
                'user_id': user_ids[1],
                'role_name': test_role['name'],
                'service_name': test_role['service_name']
            }
        ],
        'expires_at': expires_at,
        'reason': 'Temporary access for project'
    }
    
    response = api_client.post('api/admin/bulk/assign-roles/', bulk_data)
    
    assert response['status'] == 201
    result = response['json']
    assert result['success'] == 2
    
    # Verify roles have expiration
    for user_id in user_ids:
        response = api_client.get(f'api/admin/users/{user_id}/roles/')
        user_roles = response['json']
        assert len(user_roles) > 0
        assert user_roles[0]['expires_at'] is not None


def test_bulk_assign_with_some_failures(page, api_client, admin_auth_cookies):
    """Test bulk assignment with some failures"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Create one user
    timestamp = int(time.time())
    user_data = {
        'username': f'mixeduser_{timestamp}',
        'email': f'mixed_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    valid_user_id = response['json']['id']
    
    # Get a role
    response = api_client.get('api/admin/roles/')
    roles = response['json']
    test_role = next((r for r in roles if r['name'] != 'identity_admin'), None)
    
    if not test_role:
        pytest.skip("No suitable roles available")
    
    # First assign the role to create a duplicate scenario
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name']
    }
    response = api_client.post(f'api/admin/users/{valid_user_id}/roles/', role_data)
    assert response['status'] == 201
    
    # Now try bulk assignment with:
    # 1. Valid user but duplicate role (should fail)
    # 2. Invalid user ID (should fail)
    # 3. Invalid role (should fail)
    
    bulk_data = {
        'assignments': [
            {
                'user_id': valid_user_id,
                'role_name': test_role['name'],  # Duplicate
                'service_name': test_role['service_name']
            },
            {
                'user_id': 99999,  # Invalid user
                'role_name': test_role['name'],
                'service_name': test_role['service_name']
            },
            {
                'user_id': valid_user_id,
                'role_name': 'invalid_role_name',  # Invalid role
                'service_name': 'invalid_service'
            }
        ]
    }
    
    response = api_client.post('api/admin/bulk/assign-roles/', bulk_data)
    
    # Should still return 201 but with errors
    assert response['status'] == 201
    result = response['json']
    
    assert result['success'] == 0
    assert result['failed'] == 3
    assert len(result['errors']) == 3
    
    # Check error messages
    errors = result['errors']
    error_messages = [e['error'] for e in errors]
    
    # Should have errors for duplicate, invalid user, and invalid role
    assert any('already assigned' in msg.lower() for msg in error_messages)
    assert any('user' in msg.lower() for msg in error_messages)
    assert any('role' in msg.lower() for msg in error_messages)


def test_bulk_assign_validation_error(page, api_client, admin_auth_cookies):
    """Test bulk assignment with validation errors"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Missing required fields
    bulk_data = {
        'assignments': [
            {
                'user_id': 1
                # Missing role_name and service_name
            }
        ]
    }
    
    response = api_client.post('api/admin/bulk/assign-roles/', bulk_data)
    
    assert response['status'] == 400
    assert 'assignments' in response['json'] or 'error' in response['json']


def test_bulk_assign_empty_list(page, api_client, admin_auth_cookies):
    """Test bulk assignment with empty list"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    bulk_data = {
        'assignments': []
    }
    
    response = api_client.post('api/admin/bulk/assign-roles/', bulk_data)
    
    # Should either return 400 or 201 with 0 success
    if response['status'] == 201:
        result = response['json']
        assert result['success'] == 0
        assert result['failed'] == 0
    else:
        assert response['status'] == 400


def test_audit_log_access(page, api_client, admin_auth_cookies):
    """Test accessing audit log"""
    # Set admin cookies
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Try to access audit log
    response = api_client.get('api/admin/audit-log/')
    
    # Should return 200 even if empty or not implemented
    assert response['status'] == 200
    
    # Response should be JSON
    data = response['json']
    assert isinstance(data, (list, dict))
    
    # If it's a dict, might have results key
    if isinstance(data, dict):
        assert 'results' in data or 'message' in data or 'events' in data
    
    # If it's implemented, verify structure
    if isinstance(data, list) and len(data) > 0:
        event = data[0]
        # Typical audit log fields
        expected_fields = ['timestamp', 'user', 'action', 'resource']
        for field in expected_fields:
            if field in event:
                assert event[field] is not None


def test_audit_log_requires_admin(page, api_client, regular_auth_cookies):
    """Test that audit log requires admin access"""
    # Set regular user cookies
    if not regular_auth_cookies:
        pytest.skip("Regular user not available")
    
    for name, value in regular_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    # Try to access audit log as regular user
    response = api_client.get('api/admin/audit-log/')
    
    assert response['status'] == 403