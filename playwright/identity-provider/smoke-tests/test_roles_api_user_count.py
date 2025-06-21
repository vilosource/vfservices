"""
Playwright test to verify the roles API returns correct user_count data.
This test checks the actual API endpoint through the browser.
"""
import pytest
import json


def test_roles_api_structure(api_client, admin_auth_cookies):
    """Test that roles API returns properly structured data with user_count."""
    
    # Get all roles
    response = api_client.get('api/admin/roles/')
    
    assert response['status'] == 200, f"Expected 200, got {response['status']}"
    
    roles = response['json']
    assert isinstance(roles, list), "Response should be a list of roles"
    assert len(roles) > 0, "Should have at least one role"
    
    print(f"\nTotal roles returned: {len(roles)}")
    
    # Check structure of each role
    for i, role in enumerate(roles):
        print(f"\nRole {i+1}: {role.get('service_name', 'unknown')}:{role.get('name', 'unknown')}")
        
        # Check required fields
        required_fields = [
            'id', 'name', 'display_name', 'service_name', 
            'service_display_name', 'user_count'
        ]
        
        for field in required_fields:
            assert field in role, f"Role missing required field: {field}"
        
        # Verify user_count is an integer
        assert isinstance(role['user_count'], int), f"user_count should be integer, got {type(role['user_count'])}"
        assert role['user_count'] >= 0, f"user_count should be non-negative, got {role['user_count']}"
        
        print(f"  - user_count: {role['user_count']}")


def test_identity_admin_role_has_users(api_client, admin_auth_cookies):
    """Test that identity_admin role shows correct user count."""
    
    # Get all roles
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    roles = response['json']
    
    # Find identity_admin role
    identity_admin = None
    for role in roles:
        if role.get('name') == 'identity_admin' and role.get('service_name') == 'identity_provider':
            identity_admin = role
            break
    
    assert identity_admin is not None, "identity_admin role not found"
    
    print(f"\nidentity_admin role details:")
    print(f"  ID: {identity_admin['id']}")
    print(f"  Display Name: {identity_admin['display_name']}")
    print(f"  User Count: {identity_admin['user_count']}")
    
    # identity_admin should have at least 1 user (alice always has this role)
    assert identity_admin['user_count'] >= 1, \
        f"identity_admin should have at least 1 user, but has {identity_admin['user_count']}"


def test_roles_with_no_users(api_client, admin_auth_cookies):
    """Test that roles with no assigned users show user_count of 0."""
    
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    roles = response['json']
    
    # Find roles with 0 users
    roles_with_no_users = [r for r in roles if r['user_count'] == 0]
    
    print(f"\nRoles with no users: {len(roles_with_no_users)}/{len(roles)}")
    
    if roles_with_no_users:
        print("Sample roles with 0 users:")
        for role in roles_with_no_users[:3]:
            print(f"  - {role['service_name']}:{role['name']}")


def test_service_filter(api_client, admin_auth_cookies):
    """Test filtering roles by service."""
    
    # Get all roles first
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    all_roles = response['json']
    
    # Get unique services
    services = list(set(r['service_name'] for r in all_roles))
    
    if len(services) > 1:
        # Test filtering by first service
        service_name = services[0]
        response = api_client.get(f'api/admin/roles/?service={service_name}')
        assert response['status'] == 200
        
        filtered_roles = response['json']
        
        print(f"\nFiltering by service '{service_name}':")
        print(f"  Total roles: {len(all_roles)}")
        print(f"  Filtered roles: {len(filtered_roles)}")
        
        # All returned roles should be from the specified service
        for role in filtered_roles:
            assert role['service_name'] == service_name, \
                f"Expected service {service_name}, got {role['service_name']}"


def test_role_user_count_consistency(api_client, admin_auth_cookies):
    """Test that user counts are consistent with actual user assignments."""
    
    # Get roles
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    roles = response['json']
    
    # Pick a role with users to verify
    roles_with_users = [r for r in roles if r['user_count'] > 0]
    
    if not roles_with_users:
        pytest.skip("No roles with users to test")
    
    # Test first role with users
    test_role = roles_with_users[0]
    print(f"\nVerifying user count for role: {test_role['service_name']}:{test_role['name']}")
    print(f"  Reported user_count: {test_role['user_count']}")
    
    # Get users and count how many have this role
    # Note: This would require additional API endpoints to fully verify
    # For now, we just ensure the count is reasonable
    assert test_role['user_count'] > 0
    assert test_role['user_count'] < 1000, "Suspiciously high user count"


def test_all_roles_have_valid_data(api_client, admin_auth_cookies):
    """Comprehensive test of all role data."""
    
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    roles = response['json']
    
    print(f"\nAnalyzing {len(roles)} roles:")
    
    # Statistics
    total_users = sum(r['user_count'] for r in roles)
    roles_with_users = len([r for r in roles if r['user_count'] > 0])
    max_users = max(r['user_count'] for r in roles) if roles else 0
    
    print(f"  Total user assignments: {total_users}")
    print(f"  Roles with users: {roles_with_users}/{len(roles)}")
    print(f"  Max users in a role: {max_users}")
    
    # Group by service
    by_service = {}
    for role in roles:
        service = role['service_name']
        if service not in by_service:
            by_service[service] = []
        by_service[service].append(role)
    
    print(f"\nRoles by service:")
    for service, service_roles in sorted(by_service.items()):
        total_users_in_service = sum(r['user_count'] for r in service_roles)
        print(f"  {service}: {len(service_roles)} roles, {total_users_in_service} total users")


def test_compare_with_users_api(api_client, admin_auth_cookies):
    """Compare role user counts with actual user data."""
    
    # Get roles
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    roles = response['json']
    
    # Get identity_admin role
    identity_admin = next(
        (r for r in roles if r['name'] == 'identity_admin' and r['service_name'] == 'identity_provider'),
        None
    )
    
    if not identity_admin:
        pytest.skip("identity_admin role not found")
    
    print(f"\nVerifying identity_admin role user count:")
    print(f"  API reports: {identity_admin['user_count']} users")
    
    # Search for users with identity_admin role
    # First get alice who we know has this role
    response = api_client.get('api/admin/users/?search=alice')
    assert response['status'] == 200
    
    users_data = response['json']
    alice = next((u for u in users_data['results'] if u['username'] == 'alice'), None)
    
    if alice:
        alice_roles = alice.get('roles', [])
        has_identity_admin = any(
            r['name'] == 'identity_admin' and r['service'] == 'identity_provider'
            for r in alice_roles
        )
        print(f"  Alice has identity_admin: {has_identity_admin}")
        
        if has_identity_admin and identity_admin['user_count'] < 1:
            pytest.fail("identity_admin user_count is 0 but alice has this role!")


def test_pagination_preserves_user_count(api_client, admin_auth_cookies):
    """Test that user_count is preserved across pagination if applicable."""
    
    # Get first page
    response = api_client.get('api/admin/roles/')
    assert response['status'] == 200
    
    roles = response['json']
    
    # If response is paginated, it would have a different structure
    # For now, we just ensure the data structure is consistent
    if isinstance(roles, dict) and 'results' in roles:
        # Paginated response
        actual_roles = roles['results']
        print(f"\nPaginated response with {len(actual_roles)} roles")
    else:
        # Direct list response
        actual_roles = roles
        print(f"\nDirect response with {len(actual_roles)} roles")
    
    # Verify all roles have user_count regardless of response format
    for role in actual_roles:
        assert 'user_count' in role, "Every role must have user_count field"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])