#!/usr/bin/env python
"""
Setup demo users for RBAC-ABAC demonstration
"""

import os
import sys
import django

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'identity-provider.main.settings')
django.setup()

from django.contrib.auth.models import User
from identity_app.models import Service, Role, UserRole, UserAttribute
from identity_app.services import AttributeService
import json

def setup_demo_users():
    """Create demo users and assign roles/attributes"""
    
    # Get or create admin user for granting roles
    admin, _ = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@vfservices.com', 'is_superuser': True, 'is_staff': True}
    )
    
    # Get services
    try:
        billing_service = Service.objects.get(name='billing_api')
        inventory_service = Service.objects.get(name='inventory_api')
    except Service.DoesNotExist as e:
        print(f"Error: Services not registered - {e}")
        return
    
    # Create users
    users_data = {
        'alice': {
            'email': 'alice@vfservices.com',
            'first_name': 'Alice',
            'last_name': 'Manager',
            'password': 'alice123'
        },
        'bob': {
            'email': 'bob@vfservices.com',
            'first_name': 'Bob',
            'last_name': 'Billing',
            'password': 'bob123'
        },
        'charlie': {
            'email': 'charlie@vfservices.com',
            'first_name': 'Charlie',
            'last_name': 'Warehouse',
            'password': 'charlie123'
        },
        'david': {
            'email': 'david@vfservices.com',
            'first_name': 'David',
            'last_name': 'Support',
            'password': 'david123'
        }
    }
    
    users = {}
    for username, data in users_data.items():
        user, created = User.objects.get_or_create(
            username=username,
            defaults={'email': data['email'], 'first_name': data['first_name'], 'last_name': data['last_name']}
        )
        if created:
            user.set_password(data['password'])
            user.save()
            print(f"Created user: {username}")
        else:
            print(f"User already exists: {username}")
        users[username] = user
    
    # Assign roles
    roles_assignments = {
        'alice': [
            ('billing_api', 'billing_admin'),
            ('inventory_api', 'inventory_manager'),
            ('billing_api', 'customer_manager')
        ],
        'bob': [
            ('billing_api', 'invoice_manager'),
            ('billing_api', 'payment_processor'),
            ('billing_api', 'invoice_sender'),
            ('inventory_api', 'stock_viewer')
        ],
        'charlie': [
            ('inventory_api', 'warehouse_manager'),
            ('inventory_api', 'stock_adjuster'),
            ('inventory_api', 'movement_approver'),
            ('inventory_api', 'count_supervisor')
        ],
        'david': [
            ('billing_api', 'invoice_viewer'),
            ('billing_api', 'payment_viewer'),
            ('inventory_api', 'product_viewer'),
            ('inventory_api', 'stock_viewer')
        ]
    }
    
    for username, role_list in roles_assignments.items():
        user = users[username]
        print(f"\nAssigning roles to {username}:")
        for service_name, role_name in role_list:
            try:
                service = Service.objects.get(name=service_name)
                role = Role.objects.get(service=service, name=role_name)
                user_role, created = UserRole.objects.update_or_create(
                    user=user,
                    role=role,
                    defaults={'granted_by': admin}
                )
                print(f"  - {service_name}: {role_name} {'(created)' if created else '(updated)'}")
            except (Service.DoesNotExist, Role.DoesNotExist) as e:
                print(f"  - ERROR: {service_name}: {role_name} - {e}")
    
    # Set user attributes
    attributes_data = {
        'alice': {
            'department': 'Management',
            'customer_ids': [100, 200, 300, 400, 500],
            'warehouse_ids': [1, 2],
            'invoice_limit': 50000,
            'max_refund_amount': 10000,
            'can_export_data': True
        },
        'bob': {
            'department': 'Finance',
            'customer_ids': [100, 200, 300],
            'invoice_limit': 5000,
            'payment_methods': ['credit_card', 'bank_transfer'],
            'max_refund_amount': 1000
        },
        'charlie': {
            'department': 'Operations',
            'warehouse_ids': [1],
            'product_categories': ['compute', 'storage'],
            'max_adjustment_value': 5000,
            'movement_types': ['migration', 'decommission', 'reallocation'],
            'can_export_data': False
        },
        'david': {
            'department': 'Support',
            'customer_ids': [100],
            'warehouse_ids': [],
            'invoice_limit': 0,
            'can_export_data': False
        }
    }
    
    attr_service = AttributeService()
    
    for username, attrs in attributes_data.items():
        user = users[username]
        print(f"\nSetting attributes for {username}:")
        for attr_name, attr_value in attrs.items():
            try:
                # Set as global attribute (no service specified)
                attr_service.set_user_attribute(
                    user=user,
                    name=attr_name,
                    value=attr_value,
                    service=None,
                    updated_by=admin
                )
                print(f"  - {attr_name}: {attr_value}")
            except Exception as e:
                print(f"  - ERROR setting {attr_name}: {e}")
    
    print("\nDemo users setup complete!")

if __name__ == '__main__':
    setup_demo_users()