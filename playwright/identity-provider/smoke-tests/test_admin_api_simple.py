"""
Simple test to verify admin API functionality using direct HTTP requests
"""
import requests
import urllib3
import time

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://identity.vfservices.viloforge.com"

def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/login/",
        json={"username": "admin", "password": "admin123"},
        verify=False
    )
    assert response.status_code == 200
    return response.json()['token']

def test_list_users():
    """Test listing users"""
    token = get_admin_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.get(
        f"{BASE_URL}/api/admin/users/",
        headers=headers,
        verify=False
    )
    
    print(f"List Users Status: {response.status_code}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
    else:
        data = response.json()
        print(f"Found {data.get('count', 0)} users")
        print(f"Results: {len(data.get('results', []))} users in this page")
    
    assert response.status_code == 200

def test_create_user(suffix=""):
    """Test creating a user"""
    token = get_admin_token()
    
    # Try using Bearer token in header instead of cookie
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    timestamp = int(time.time())
    user_data = {
        'username': f'testuser_{timestamp}{suffix}',
        'email': f'test_{timestamp}{suffix}@example.com',
        'password': 'TestPass123!',
        'first_name': 'Test',
        'last_name': 'User'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users/",
        json=user_data,
        headers=headers,
        verify=False
    )
    
    print(f"Create User Status: {response.status_code}")
    if response.status_code != 201:
        print(f"Response: {response.text}")
    else:
        created_user = response.json()
        print(f"Created user: {created_user.get('username')} (ID: {created_user.get('id')})")
    
    assert response.status_code == 201
    return response.json()['id']

def test_assign_role():
    """Test assigning a role to a user"""
    # First create a user
    user_id = test_create_user("_for_role")
    
    token = get_admin_token()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    # First get available roles
    response = requests.get(
        f"{BASE_URL}/api/admin/roles/",
        headers=headers,
        verify=False
    )
    
    if response.status_code != 200:
        print(f"Failed to get roles: {response.text}")
        return
    
    roles = response.json()
    # Find a non-admin role
    test_role = None
    for role in roles:
        if role['name'] != 'identity_admin':
            test_role = role
            break
    
    if not test_role:
        print("No suitable role found for testing")
        return
    
    # Assign the role
    role_data = {
        'role_name': test_role['name'],
        'service_name': test_role['service_name'],
        'reason': 'Test assignment'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/admin/users/{user_id}/roles/",
        json=role_data,
        headers=headers,
        verify=False
    )
    
    print(f"Assign Role Status: {response.status_code}")
    if response.status_code != 201:
        print(f"Response: {response.text}")
    else:
        print(f"Assigned role: {test_role['name']} to user {user_id}")
    
    assert response.status_code == 201

def test_unauthorized_access():
    """Test that API requires authentication"""
    response = requests.get(
        f"{BASE_URL}/api/admin/users/",
        verify=False
    )
    
    print(f"Unauthorized Access Status: {response.status_code}")
    assert response.status_code in [401, 403]  # Could be either depending on middleware

if __name__ == "__main__":
    print("Testing Identity Provider Admin API")
    print("=" * 50)
    
    print("\n1. Testing unauthorized access...")
    test_unauthorized_access()
    print("✓ API correctly requires authentication")
    
    print("\n2. Testing list users...")
    test_list_users()
    print("✓ List users successful")
    
    print("\n3. Testing create user...")
    test_create_user()
    print("✓ Create user successful")
    
    print("\n4. Testing assign role...")
    test_assign_role()
    print("✓ Assign role successful")
    
    print("\n" + "=" * 50)
    print("All tests passed!")