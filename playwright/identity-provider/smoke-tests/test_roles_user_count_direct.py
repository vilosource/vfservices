"""
Direct Playwright test to verify roles API user_count values.
This test fetches the actual API response and checks that user counts are not all zero.
"""
import pytest
from playwright.sync_api import sync_playwright
import json


def test_roles_api_user_count_not_zero():
    """Test that roles API returns non-zero user counts"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # First, login to get authentication
            print("\n1. Logging in...")
            login_response = page.request.post(
                "https://identity.vfservices.viloforge.com/api/login/",
                data={
                    "username": "admin",
                    "password": "admin123"
                }
            )
            
            if login_response.status != 200:
                print(f"   ❌ Login failed: {login_response.status}")
                print(f"   Response: {login_response.text()}")
                pytest.fail("Login failed")
            
            print("   ✅ Login successful")
            
            # The API might return token in response body instead of cookie
            login_data = login_response.json()
            token = login_data.get('token')
            
            if not token:
                # Try getting from cookies
                cookies = context.cookies()
                jwt_cookie = next((c for c in cookies if c['name'] == 'jwt'), None)
                
                if jwt_cookie:
                    token = jwt_cookie['value']
                else:
                    # Check if token is in the response headers
                    set_cookie = login_response.headers.get('set-cookie', '')
                    print(f"   Set-Cookie header: {set_cookie}")
                    print(f"   Response body: {login_data}")
                    pytest.fail("No JWT token found in response or cookies")
            
            print(f"   ✅ JWT token obtained")
            
            # Now fetch the roles API
            print("\n2. Fetching roles API...")
            roles_response = page.request.get(
                "https://identity.vfservices.viloforge.com/api/admin/roles/",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if roles_response.status != 200:
                print(f"   ❌ Roles API failed: {roles_response.status}")
                print(f"   Response: {roles_response.text()}")
                pytest.fail(f"Roles API returned {roles_response.status}")
            
            # Parse the response
            roles = roles_response.json()
            print(f"   ✅ Got {len(roles)} roles")
            
            # Analyze the data
            print("\n3. Analyzing user counts...")
            
            # Check if any role has user_count > 0
            roles_with_users = [r for r in roles if r.get('user_count', 0) > 0]
            roles_without_field = [r for r in roles if 'user_count' not in r]
            
            if roles_without_field:
                print(f"   ⚠️  {len(roles_without_field)} roles missing user_count field")
                for r in roles_without_field[:3]:
                    print(f"      - {r.get('service_name', 'unknown')}:{r.get('name', 'unknown')}")
            
            print(f"   Roles with users: {len(roles_with_users)}/{len(roles)}")
            
            # Find specific roles we know should have users
            identity_admin = next(
                (r for r in roles if r.get('name') == 'identity_admin' and r.get('service_name') == 'identity_provider'),
                None
            )
            
            if identity_admin:
                print(f"\n4. identity_admin role:")
                print(f"   - ID: {identity_admin['id']}")
                print(f"   - user_count: {identity_admin.get('user_count', 'MISSING')}")
                print(f"   - Full data: {json.dumps(identity_admin, indent=2)}")
                
                # This role should definitely have users (alice has it)
                assert 'user_count' in identity_admin, "identity_admin role missing user_count field"
                assert identity_admin['user_count'] > 0, f"identity_admin should have users but has {identity_admin['user_count']}"
            else:
                pytest.fail("identity_admin role not found in response")
            
            # Check alice's roles specifically
            print("\n5. Checking alice user...")
            alice_response = page.request.get(
                "https://identity.vfservices.viloforge.com/api/admin/users/?search=alice",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if alice_response.status == 200:
                data = alice_response.json()
                users = data.get('results', [])
                alice = next((u for u in users if u['username'] == 'alice'), None)
                
                if alice:
                    print(f"   ✅ Alice found (ID: {alice['id']})")
                    alice_roles = alice.get('roles', [])
                    print(f"   Alice has {len(alice_roles)} roles:")
                    
                    for role in alice_roles:
                        print(f"      - {role.get('service', 'unknown')}:{role.get('name', 'unknown')}")
                        
                        # Find this role in the roles list and check its count
                        matching_role = next(
                            (r for r in roles if r['name'] == role['name'] and 
                             r.get('service_name') == role.get('service')),
                            None
                        )
                        if matching_role:
                            count = matching_role.get('user_count', 0)
                            print(f"        → user_count in roles API: {count}")
                            if count == 0:
                                print(f"        ⚠️  WARNING: This role shows 0 users but alice has it!")
            
            # Summary statistics
            print("\n6. Summary:")
            total_user_assignments = sum(r.get('user_count', 0) for r in roles)
            print(f"   Total user assignments across all roles: {total_user_assignments}")
            
            if total_user_assignments == 0:
                print("   ❌ PROBLEM: All roles show 0 users!")
                print("\n   Dumping first 3 roles for debugging:")
                for i, role in enumerate(roles[:3]):
                    print(f"\n   Role {i+1}:")
                    print(json.dumps(role, indent=4))
                
                pytest.fail("All roles have user_count of 0, which is incorrect")
            
            # Show roles with highest user counts
            top_roles = sorted(roles, key=lambda r: r.get('user_count', 0), reverse=True)[:5]
            print("\n   Top roles by user count:")
            for r in top_roles:
                if r.get('user_count', 0) > 0:
                    print(f"      - {r['service_name']}:{r['name']} = {r['user_count']} users")
            
            # Final assertion
            assert len(roles_with_users) > 0, "No roles have any users assigned"
            print(f"\n   ✅ SUCCESS: Found {len(roles_with_users)} roles with users")
            
        finally:
            browser.close()


def test_debug_role_counts():
    """Debug test to understand why counts might be 0"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Login
            login_response = page.request.post(
                "https://identity.vfservices.viloforge.com/api/login/",
                data={
                    "username": "admin",
                    "password": "admin123"
                }
            )
            
            assert login_response.status == 200, "Login failed"
            
            # Get token from response
            login_data = login_response.json()
            token = login_data.get('token')
            assert token, "No token in login response"
            
            # Get all users and count their roles
            print("\nDebug: Counting actual user role assignments...")
            
            # Get first page of users
            users_response = page.request.get(
                "https://identity.vfservices.viloforge.com/api/admin/users/",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {token}"
                }
            )
            
            if users_response.status == 200:
                data = users_response.json()
                users = data.get('results', [])
                
                # Count roles across users
                role_counts = {}
                for user in users:
                    user_roles = user.get('roles', [])
                    for role in user_roles:
                        key = f"{role.get('service', 'unknown')}:{role.get('name', 'unknown')}"
                        role_counts[key] = role_counts.get(key, 0) + 1
                
                print(f"Found {len(users)} users in first page")
                print(f"Role distribution from user data:")
                for role_key, count in sorted(role_counts.items(), key=lambda x: x[1], reverse=True):
                    print(f"   - {role_key}: {count} users")
                
                # Now compare with roles API
                roles_response = page.request.get(
                    "https://identity.vfservices.viloforge.com/api/admin/roles/",
                    headers={
                        "Accept": "application/json",
                        "Authorization": f"Bearer {token}"
                    }
                )
                
                if roles_response.status == 200:
                    roles = roles_response.json()
                    
                    print(f"\nComparing with roles API data:")
                    for role in roles:
                        key = f"{role.get('service_name')}:{role.get('name')}"
                        expected = role_counts.get(key, 0)
                        actual = role.get('user_count', 0)
                        
                        if key in role_counts:
                            if expected != actual:
                                print(f"   ❌ {key}: Expected {expected}, got {actual}")
                            else:
                                print(f"   ✅ {key}: Correct count {actual}")
                
        finally:
            browser.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])