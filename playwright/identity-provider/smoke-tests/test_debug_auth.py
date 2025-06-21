"""
Debug authentication issues
"""
import requests
import urllib3
import json

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://identity.vfservices.viloforge.com"

def test_cookie_auth():
    """Test authentication with cookie"""
    # Get token
    response = requests.post(
        f"{BASE_URL}/api/login/",
        json={"username": "admin", "password": "admin123"},
        verify=False
    )
    
    print(f"Login response: {response.status_code}")
    token = response.json().get('token')
    print(f"Token: {token[:50]}...")
    
    # Test with cookie
    cookies = {'jwt': token}
    response = requests.get(
        f"{BASE_URL}/api/admin/users/",
        cookies=cookies,
        verify=False
    )
    
    print(f"\nWith Cookie - Status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    if response.status_code != 200:
        print(f"Response: {response.text}")
    
    # Also test the profile endpoint to see if auth works at all
    response = requests.get(
        f"{BASE_URL}/api/profile/",
        cookies=cookies,
        verify=False
    )
    
    print(f"\nProfile endpoint - Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Profile: {response.json()}")
    else:
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_cookie_auth()