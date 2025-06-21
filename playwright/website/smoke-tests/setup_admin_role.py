#!/usr/bin/env python
"""
Script to grant identity_admin role to the admin user
"""
import requests
import json

# First, login as admin
login_url = "https://identity.vfservices.viloforge.com/api/login/"
login_data = {
    "username": "admin",
    "password": "admin123"
}

# Disable SSL warnings for self-signed certificates
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("Logging in as admin...")
response = requests.post(login_url, json=login_data, verify=False)
if response.status_code != 200:
    print(f"Login failed: {response.status_code} - {response.text}")
    exit(1)

# Get the JWT token from the response
jwt_token = response.cookies.get('jwt') or response.cookies.get('jwt_token')
print(f"Response cookies: {response.cookies}")
print(f"Response headers: {response.headers}")
print(f"Response body: {response.json()}")

if not jwt_token:
    # Try to get token from response body
    response_data = response.json()
    jwt_token = response_data.get('token') or response_data.get('jwt')
    
if not jwt_token:
    print("No JWT token received")
    exit(1)

print("Login successful!")

# Now grant the identity_admin role to the admin user
# First get the admin user ID
profile_url = "https://identity.vfservices.viloforge.com/api/profile/"
headers = {
    "Authorization": f"Bearer {jwt_token}"
}

print("Getting admin user profile...")
response = requests.get(profile_url, headers=headers, verify=False)
if response.status_code != 200:
    print(f"Failed to get profile: {response.status_code} - {response.text}")
    exit(1)

# The user_id is in the JWT payload
import base64
jwt_payload = jwt_token.split('.')[1]
# Add padding if needed
jwt_payload += '=' * (4 - len(jwt_payload) % 4)
payload_data = json.loads(base64.b64decode(jwt_payload))
user_id = payload_data.get('user_id')
print(f"JWT payload: {payload_data}")
print(f"Admin user ID: {user_id}")

# The identity provider service is named 'identity_provider'
service_name = 'identity_provider'

# Now assign the identity_admin role
assign_role_url = f"https://identity.vfservices.viloforge.com/api/admin/users/{user_id}/roles/"
role_data = {
    "role_name": "identity_admin",
    "service_name": service_name
}

print("Assigning identity_admin role...")
response = requests.post(assign_role_url, json=role_data, headers=headers, verify=False)
if response.status_code == 201:
    print("Successfully granted identity_admin role to admin user!")
elif response.status_code == 400 and "already has role" in response.text:
    print("Admin user already has identity_admin role")
else:
    print(f"Failed to assign role: {response.status_code} - {response.text}")

# Refresh the user cache to ensure changes take effect
refresh_url = "https://identity.vfservices.viloforge.com/api/refresh-user-cache/"
print("Refreshing user cache...")
response = requests.post(refresh_url, json={"user_id": user_id, "service_name": service_name}, headers=headers, verify=False)
if response.status_code == 200:
    print("User cache refreshed successfully!")
else:
    print(f"Failed to refresh cache: {response.status_code} - {response.text}")

print("\nSetup complete! The admin user now has identity_admin privileges.")