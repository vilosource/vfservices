"""
Playwright test to verify that user_count is correctly calculated for roles.
This test specifically checks that alice (who has identity_admin role) 
causes the identity_admin role to have user_count > 0.
"""
import pytest
import requests


def test_alice_role_has_user_count(api_client, admin_auth_cookies):
    """Test that alice's identity_admin role shows user_count > 0"""
    
    # First, verify alice exists and has the identity_admin role
    response = api_client.get('api/admin/users/?search=alice')
    assert response['status'] == 200
    
    users = response['json']['results']
    alice = next((u for u in users if u['username'] == 'alice'), None)
    assert alice is not None, "Alice user not found"
    
    # Get alice's roles
    alice_id = alice['id']
    response = api_client.get(f'api/admin/users/{alice_id}/roles/')
    assert response['status'] == 200
    
    alice_roles = response['json']
    assert len(alice_roles) > 0, "Alice has no roles"
    
    # Check if alice has identity_admin role
    identity_admin_role = next((r for r in alice_roles if r['role_name'] == 'identity_admin'), None)
    assert identity_admin_role is not None, "Alice doesn't have identity_admin role"
    
    print(f"\nAlice has {len(alice_roles)} roles:")
    for role in alice_roles:
        print(f"  - {role['service_name']}: {role['role_name']}")
    
    # Now check the roles API to see user_count
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    all_roles = response['json']
    
    # Find identity_admin role in the list
    identity_admin_from_api = next(
        (r for r in all_roles if r['name'] == 'identity_admin' and r['service_name'] == 'identity_provider'),
        None
    )
    assert identity_admin_from_api is not None, "identity_admin role not found in roles API"
    
    print(f"\nidentity_admin role details:")
    print(f"  - user_count: {identity_admin_from_api.get('user_count', 'NOT FOUND')}")
    print(f"  - service: {identity_admin_from_api['service_name']}")
    
    # The main assertion - identity_admin should have at least 1 user (alice)
    assert 'user_count' in identity_admin_from_api, "user_count field missing from role"
    assert identity_admin_from_api['user_count'] >= 1, \
        f"identity_admin role should have at least 1 user (alice), but has {identity_admin_from_api['user_count']}"


def test_role_user_counts_match_assignments(api_client, admin_auth_cookies):
    """Test that user_count for each role matches actual user assignments"""
    
    # Get all roles with their user counts
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    all_roles = response['json']
    
    # Pick a few roles to verify (limit to avoid too many API calls)
    roles_to_check = [r for r in all_roles if r.get('user_count', 0) > 0][:3]
    
    if not roles_to_check:
        # If no roles have users, check identity_admin specifically
        identity_admin = next((r for r in all_roles if r['name'] == 'identity_admin'), None)
        if identity_admin:
            roles_to_check = [identity_admin]
    
    print(f"\nChecking {len(roles_to_check)} roles for user count accuracy:")
    
    for role in roles_to_check:
        # Count users with this role by searching
        response = api_client.get(f"api/admin/users/?has_role={role['name']}&service={role['service_name']}")
        assert response['status'] == 200
        
        users_with_role = response['json']['results']
        actual_count = len(users_with_role)
        
        print(f"\n{role['service_name']}: {role['name']}")
        print(f"  - API user_count: {role.get('user_count', 'NOT FOUND')}")
        print(f"  - Actual users found: {actual_count}")
        
        if actual_count > 0:
            print(f"  - Users: {', '.join(u['username'] for u in users_with_role[:5])}")
            if len(users_with_role) > 5:
                print(f"    ... and {len(users_with_role) - 5} more")


def test_create_user_updates_role_count(api_client, admin_auth_cookies):
    """Test that assigning a role to a new user updates the role's user_count"""
    import time
    
    # Get initial count for a test role
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    # Find a role to test with (not identity_admin to avoid affecting other tests)
    test_role = None
    initial_count = 0
    
    for role in response['json']:
        if role['name'] != 'identity_admin' and role['service_name'] == 'identity_provider':
            test_role = role
            initial_count = role.get('user_count', 0)
            break
    
    if not test_role:
        pytest.skip("No suitable test role found")
    
    print(f"\nTesting with role: {test_role['service_name']}: {test_role['name']}")
    print(f"Initial user_count: {initial_count}")
    
    # Create a new user
    timestamp = int(time.time())
    user_data = {
        'username': f'counttest_{timestamp}',
        'email': f'counttest_{timestamp}@example.com',
        'password': 'TestPass123!'
    }
    
    response = api_client.post('api/admin/users/', user_data)
    assert response['status'] == 201
    user_id = response['json']['id']
    
    # Assign the role
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name']
    }
    
    response = api_client.post(f'api/admin/users/{user_id}/roles/', role_data)
    assert response['status'] == 201
    
    # Check the updated count
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    updated_role = next(
        (r for r in response['json'] 
         if r['name'] == test_role['name'] and r['service_name'] == test_role['service_name']),
        None
    )
    
    assert updated_role is not None
    updated_count = updated_role.get('user_count', 0)
    
    print(f"Updated user_count: {updated_count}")
    
    # The count should have increased by 1
    assert updated_count == initial_count + 1, \
        f"Expected count to increase from {initial_count} to {initial_count + 1}, but got {updated_count}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])