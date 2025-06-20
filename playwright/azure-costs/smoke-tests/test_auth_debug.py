import requests
from playwright_config import Config

# Test authentication
print(f"Testing authentication for user: {Config.TEST_USERNAME}")
print(f"Identity Provider URL: {Config.IDENTITY_PROVIDER_URL}")

login_url = f"{Config.IDENTITY_PROVIDER_URL}/api/login/"
print(f"Login URL: {login_url}")

response = requests.post(
    login_url,
    json={"username": Config.TEST_USERNAME, "password": Config.TEST_PASSWORD},
    verify=False
)

print(f"Response status: {response.status_code}")
print(f"Response body: {response.text}")

if response.status_code == 200:
    data = response.json()
    token = data.get("token") or data.get("access_token")
    print(f"Token received: {token[:50]}..." if token else "No token in response")
    
    # Test the token
    test_url = f"{Config.AZURE_COSTS_BASE_URL}/api/private"
    auth_response = requests.get(
        test_url,
        headers={"Authorization": f"Bearer {token}"},
        verify=False
    )
    print(f"\nTesting {test_url}")
    print(f"Auth response status: {auth_response.status_code}")
    print(f"Auth response body: {auth_response.text}")