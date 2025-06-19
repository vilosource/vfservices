#!/usr/bin/env python3
"""Check Charlie's account."""

import subprocess

# Check if Charlie exists
cmd = """
docker exec vfservices-identity-provider-1 python manage.py shell -c "
from django.contrib.auth.models import User
try:
    charlie = User.objects.get(username='charlie')
    print(f'Charlie exists: ID={charlie.id}, username={charlie.username}, email={charlie.email}')
    print(f'Is active: {charlie.is_active}')
    
    # Try to authenticate
    from django.contrib.auth import authenticate
    user = authenticate(username='charlie', password='charlie123')
    if user:
        print('Authentication with charlie123: SUCCESS')
    else:
        print('Authentication with charlie123: FAILED')
        
        # Try to set the password
        charlie.set_password('charlie123')
        charlie.save()
        print('Password reset to charlie123')
        
        # Try again
        user = authenticate(username='charlie', password='charlie123')
        if user:
            print('Authentication after reset: SUCCESS')
        else:
            print('Authentication after reset: FAILED')
            
except User.DoesNotExist:
    print('Charlie does not exist!')
"
"""

result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Error:", result.stderr)