"""
Quick test to verify the Identity Provider setup
"""
import requests
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_identity_provider_accessible():
    """Test that Identity Provider is accessible"""
    response = requests.get(
        "https://identity.vfservices.viloforge.com/api/status/",
        verify=False
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_admin_login():
    """Test admin login"""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(
        "https://identity.vfservices.viloforge.com/api/login/",
        json=login_data,
        verify=False
    )
    
    print(f"Login Status Code: {response.status_code}")
    
    if response.status_code != 200:
        print(f"Login Response: {response.text}")
    else:
        print(f"Login Response: {response.json()}")
    
    assert response.status_code == 200, f"Login failed with status {response.status_code}"
    
    # API returns token in response body, not as cookie
    token = response.json().get('token')
    assert token is not None, "JWT token not found in response"
    print(f"Token received: {token[:20]}..." if token else "No token")

if __name__ == "__main__":
    print("Testing Identity Provider setup...")
    print("=" * 50)
    
    print("\n1. Testing service accessibility...")
    try:
        test_identity_provider_accessible()
        print("✓ Identity Provider is accessible")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n2. Testing admin login...")
    try:
        test_admin_login()
        print("✓ Admin login successful")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    print("\n" + "=" * 50)
    print("Setup verification complete!")