#!/usr/bin/env python
"""
Script to add azure-costs roles to demo users for testing.
Run this after running setup_demo_users in identity-provider.
"""

import os
import sys
import django

# Add parent directory to path to import Django settings
sys.path.insert(0, '/app/identity-provider')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.contrib.auth.models import User
from identity_app.models import Service, Role, UserRole
from identity_app.services import RedisService, AttributeService

def setup_azure_costs_roles():
    """Add azure-costs roles to demo users."""
    
    # Get azure_costs service
    try:
        service = Service.objects.get(name='azure_costs')
        print(f"Found azure_costs service: {service}")
    except Service.DoesNotExist:
        print("Error: azure_costs service not found. Make sure the service is registered.")
        return
    
    # Define user role mappings
    user_roles = {
        'admin': ['costs_admin'],
        'alice': ['costs_manager'],
        'bob': ['costs_viewer'],
        'charlie': ['costs_viewer'],
        'david': ['costs_viewer']
    }
    
    # Define user attributes for azure_costs
    user_attributes = {
        'admin': {
            'azure_subscription_ids': ['sub-001', 'sub-002', 'sub-003'],
            'cost_center_ids': ['cc-001', 'cc-002', 'cc-003'],
            'budget_limit': 1000000,
            'can_export_reports': True
        },
        'alice': {
            'azure_subscription_ids': ['sub-001', 'sub-002'],
            'cost_center_ids': ['cc-001'],
            'budget_limit': 50000,
            'can_export_reports': True
        },
        'bob': {
            'azure_subscription_ids': ['sub-001'],
            'cost_center_ids': [],
            'budget_limit': 0,
            'can_export_reports': False
        },
        'charlie': {
            'azure_subscription_ids': ['sub-002'],
            'cost_center_ids': ['cc-002'],
            'budget_limit': 10000,
            'can_export_reports': False
        },
        'david': {
            'azure_subscription_ids': [],
            'cost_center_ids': [],
            'budget_limit': 0,
            'can_export_reports': False
        }
    }
    
    # Get admin user for granting roles
    admin_user = User.objects.get(username='admin')
    
    for username, role_names in user_roles.items():
        try:
            user = User.objects.get(username=username)
            print(f"\nProcessing user: {username}")
            
            # Grant roles
            for role_name in role_names:
                try:
                    role = Role.objects.get(service=service, name=role_name)
                    user_role, created = UserRole.objects.update_or_create(
                        user=user,
                        role=role,
                        defaults={'granted_by': admin_user}
                    )
                    if created:
                        print(f"  ✓ Granted role: {role_name}")
                    else:
                        print(f"  → Already has role: {role_name}")
                except Role.DoesNotExist:
                    print(f"  ✗ Role not found: {role_name}")
            
            # Set attributes
            if username in user_attributes:
                attrs = user_attributes[username]
                for attr_name, attr_value in attrs.items():
                    AttributeService.set_user_attribute(
                        user=user,
                        name=attr_name,
                        value=attr_value,
                        service=service,
                        updated_by=admin_user
                    )
                    print(f"  ✓ Set attribute: {attr_name} = {attr_value}")
            
            # Populate Redis cache
            RedisService.populate_user_attributes(user.id, service.name)
            print(f"  ✓ Populated Redis cache")
            
        except User.DoesNotExist:
            print(f"\n✗ User not found: {username}")
    
    print("\n✅ Azure costs roles setup complete!")

if __name__ == '__main__':
    setup_azure_costs_roles()