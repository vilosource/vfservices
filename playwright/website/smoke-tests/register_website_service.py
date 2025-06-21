#!/usr/bin/env python
"""
Script to register the website service with the Identity Provider
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

# Get the JWT token from the response body
token = response.json().get('token')
if not token:
    print("No JWT token received")
    exit(1)

print("Login successful!")

# Now register the website service
register_url = "https://identity.vfservices.viloforge.com/api/services/register/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

service_data = {
    "service": "website",
    "display_name": "VFServices Website",
    "description": "Main VFServices website",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "website_viewer",
            "display_name": "Website Viewer",
            "description": "Can view website content",
            "permissions": ["view_content", "view_profile"]
        },
        {
            "name": "website_admin",
            "display_name": "Website Administrator",
            "description": "Can administer website content",
            "permissions": ["view_content", "edit_content", "manage_users", "view_analytics"]
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department",
            "type": "string"
        }
    ]
}

print("Registering website service...")
response = requests.post(register_url, json=service_data, headers=headers, verify=False)

if response.status_code == 201:
    print("Website service registered successfully!")
    print(f"Response: {response.json()}")
elif response.status_code == 400 and "already exists" in response.text:
    print("Website service already registered")
else:
    print(f"Failed to register service: {response.status_code} - {response.text}")

print("\nRegistration complete!")