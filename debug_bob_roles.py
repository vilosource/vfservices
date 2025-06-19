#!/usr/bin/env python3
"""Debug Bob's roles and permissions."""

import subprocess
import json

def run_django_command(container, command):
    """Run Django management command in container."""
    cmd = ['docker', 'exec', container, 'python', 'manage.py', 'shell', '-c', command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

print("Debugging Bob's roles and permissions...\n")

# 1. Check Bob's roles in database
print("1. Checking Bob's database records...")
check_bob_cmd = """
from django.contrib.auth.models import User
from identity_app.models import UserRole, Service

bob = User.objects.get(username='bob')
print(f'Bob User ID: {bob.id}')
print(f'Bob Username: {bob.username}')

# Get all roles for Bob
roles = UserRole.objects.filter(user=bob).select_related('role__service')
print(f'\\nTotal roles: {roles.count()}')

for ur in roles:
    print(f'- {ur.role.service.name}: {ur.role.name}')
"""

stdout, stderr = run_django_command('vfservices-identity-provider-1', check_bob_cmd)
print(stdout)

# 2. Test Bob's actual access
print("\n2. Testing Bob's actual access via API...")

import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Login as Bob
login_resp = requests.post(
    "https://identity.vfservices.viloforge.com/api/login/",
    json={"username": "bob", "password": "bob123"},
    verify=False
)

if login_resp.status_code == 200:
    token = login_resp.json().get('token')
    print(f"Login successful! Token: {token[:20]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test billing access
    print("\nTesting Billing API access:")
    billing_resp = requests.get(
        "https://billing.vfservices.viloforge.com/test-rbac/",
        headers=headers,
        verify=False
    )
    
    if billing_resp.status_code == 200:
        data = billing_resp.json()
        print(f"  Status: {billing_resp.status_code}")
        if 'user_attrs' in data and data['user_attrs']:
            print(f"  Roles: {data['user_attrs'].get('roles', [])}")
        else:
            print("  No user attributes found")
    else:
        print(f"  Access denied: {billing_resp.status_code}")
    
    # Test inventory access
    print("\nTesting Inventory API access:")
    inventory_resp = requests.get(
        "https://inventory.vfservices.viloforge.com/test-rbac/",
        headers=headers,
        verify=False
    )
    
    if inventory_resp.status_code == 200:
        data = inventory_resp.json()
        print(f"  Status: {inventory_resp.status_code}")
        if 'user_attrs' in data and data['user_attrs']:
            print(f"  Roles: {data['user_attrs'].get('roles', [])}")
        else:
            print("  No user attributes found")
    else:
        print(f"  Access denied: {inventory_resp.status_code}")
else:
    print(f"Login failed: {login_resp.status_code}")