#!/usr/bin/env python
"""
Script to register the identity_provider service with itself
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

# Now register the identity_provider service
register_url = "https://identity.vfservices.viloforge.com/api/services/register/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

service_data = {
    "service": "identity_provider",
    "display_name": "Identity Provider",
    "description": "Central authentication and authorization service",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "identity_admin",
            "display_name": "Identity Administrator",
            "description": "Can manage users, roles, and services",
            "permissions": ["manage_users", "manage_roles", "manage_services", "view_audit_logs"]
        },
        {
            "name": "identity_viewer",
            "display_name": "Identity Viewer",
            "description": "Can view identity information",
            "permissions": ["view_users", "view_roles", "view_services"]
        }
    ],
    "attributes": [
        {
            "name": "admin_level",
            "display_name": "Admin Level",
            "description": "Level of administrative access",
            "type": "string"
        }
    ]
}

print("Registering identity_provider service...")
response = requests.post(register_url, json=service_data, headers=headers, verify=False)

if response.status_code == 200 or response.status_code == 201:
    print("Identity Provider service registered successfully!")
    print(f"Response: {response.json()}")
elif response.status_code == 400 and "already exists" in response.text:
    print("Identity Provider service already registered")
else:
    print(f"Failed to register service: {response.status_code} - {response.text}")

print("\nRegistration complete!")