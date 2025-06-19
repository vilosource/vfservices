#!/usr/bin/env python3
"""Debug Alice's roles and permissions."""

import subprocess
import json

def run_django_command(container, command):
    """Run Django management command in container."""
    cmd = ['docker', 'exec', container, 'python', 'manage.py', 'shell', '-c', command]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout, result.stderr

print("Debugging Alice's roles and permissions...\n")

# 1. Check Alice's user ID and roles in database
print("1. Checking Alice's database records...")
check_alice_cmd = """
from django.contrib.auth.models import User
from identity_app.models import UserRole, Service

alice = User.objects.get(username='alice')
print(f'Alice User ID: {alice.id}')
print(f'Alice Username: {alice.username}')

# Get all roles for Alice
roles = UserRole.objects.filter(user=alice).select_related('role__service')
print(f'\\nTotal roles: {roles.count()}')

for ur in roles:
    print(f'- {ur.role.service.name}: {ur.role.name}')
"""

stdout, stderr = run_django_command('vfservices-identity-provider-1', check_alice_cmd)
print(stdout)

# 2. Check Redis cache for Alice
print("\n2. Checking Redis cache...")
redis_cmd = """
from common.rbac_abac import RedisAttributeClient
from django.contrib.auth.models import User

alice = User.objects.get(username='alice')
client = RedisAttributeClient()

# Check billing_api
billing_attrs = client.get_user_attributes(alice.id, 'billing_api')
print(f'Billing API attributes cached: {billing_attrs is not None}')
if billing_attrs:
    print(f'  Roles: {billing_attrs.roles}')

# Check inventory_api  
inventory_attrs = client.get_user_attributes(alice.id, 'inventory_api')
print(f'\\nInventory API attributes cached: {inventory_attrs is not None}')
if inventory_attrs:
    print(f'  Roles: {inventory_attrs.roles}')
"""

stdout, stderr = run_django_command('vfservices-identity-provider-1', redis_cmd)
print(stdout)

# 3. Test JWT token generation
print("\n3. Testing JWT token generation...")
jwt_cmd = """
from django.contrib.auth.models import User
from identity_app.views import api_login
import json

# Simulate login
alice = User.objects.get(username='alice')
from django.test import RequestFactory
factory = RequestFactory()
request = factory.post('/api/login/', json.dumps({'username': 'alice', 'password': 'alice123'}), content_type='application/json')

# Mock the authenticate function
from unittest.mock import patch
with patch('django.contrib.auth.authenticate') as mock_auth:
    mock_auth.return_value = alice
    from identity_app.views import api_login
    response = api_login(request)
    
    if response.status_code == 200:
        import jwt
        data = json.loads(response.content)
        token = data.get('token')
        
        # Decode token
        from django.conf import settings
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=['HS256'])
        print(f'Token payload:')
        print(f'  user_id: {payload.get("user_id")}')
        print(f'  username: {payload.get("username")}')
        print(f'  email: {payload.get("email")}')
    else:
        print(f'Login failed: {response.status_code}')
"""

stdout, stderr = run_django_command('vfservices-identity-provider-1', jwt_cmd)
print(stdout)

# 4. Force refresh Redis cache
print("\n4. Force refreshing Redis cache for Alice...")
refresh_cmd = """
from identity_app.services import RedisService
from django.contrib.auth.models import User

alice = User.objects.get(username='alice')
print(f'Refreshing cache for Alice (ID: {alice.id})...')

# Refresh for all services
services = ['billing_api', 'inventory_api', 'identity_provider']
for service in services:
    success = RedisService.populate_user_attributes(alice.id, service)
    print(f'  {service}: {"Success" if success else "Failed"}')
"""

stdout, stderr = run_django_command('vfservices-identity-provider-1', refresh_cmd)
print(stdout)