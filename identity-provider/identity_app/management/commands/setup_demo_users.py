"""
Management command to set up demo users with RBAC-ABAC roles and attributes.
Based on docs/RBAC-ABAC-DEMO-USERS.md
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from identity_app.models import Service, Role, UserRole, UserAttribute
from identity_app.services import RBACService, AttributeService, RedisService
import json


class Command(BaseCommand):
    help = 'Sets up demo users with their roles and attributes for RBAC-ABAC testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset demo users (delete and recreate)',
        )
        parser.add_argument(
            '--skip-missing-services',
            action='store_true',
            help='Skip roles for services that have not registered yet',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo users...')
        
        # Demo user configurations based on docs/RBAC-ABAC-DEMO-USERS.md
        demo_users = {
            'alice': {
                'email': 'alice@example.com',
                'first_name': 'Alice',
                'last_name': 'Anderson',
                'password': 'password123',
                'roles': {
                    'billing_api': ['billing_admin'],
                    'inventory_api': ['inventory_manager'],
                    'identity_provider': ['customer_manager'],
                    'cielo_website': ['cielo_admin']  # Full CIELO access for senior manager
                },
                'attributes': {
                    'global': {
                        'department': 'Management',
                        'customer_ids': [100, 200, 300, 400, 500],
                        'warehouse_ids': [1, 2],
                        'invoice_limit': 50000,
                        'max_refund_amount': 10000,
                        'can_export_data': True
                    },
                    'cielo_website': {
                        'cloud_providers': ['aws', 'azure', 'gcp'],
                        'cost_center_ids': [1000, 2000, 3000],
                        'max_resource_cost': 100000,
                        'can_provision_resources': True
                    }
                }
            },
            'bob': {
                'email': 'bob@example.com',
                'first_name': 'Bob',
                'last_name': 'Brown',
                'password': 'password123',
                'roles': {
                    'billing_api': ['invoice_manager', 'payment_processor', 'invoice_sender'],
                    'inventory_api': ['stock_viewer'],
                    'cielo_website': ['cost_analyst']  # Can analyze cloud costs in CIELO
                },
                'attributes': {
                    'global': {
                        'department': 'Finance',
                        'customer_ids': [100, 200, 300],
                        'invoice_limit': 5000,
                        'payment_methods': ['credit_card', 'bank_transfer'],
                        'max_refund_amount': 1000
                    },
                    'cielo_website': {
                        'cloud_providers': ['azure'],
                        'cost_center_ids': [1000, 2000],
                        'max_resource_cost': 0,  # Can't provision, only analyze
                        'can_provision_resources': False
                    }
                }
            },
            'charlie': {
                'email': 'charlie@example.com',
                'first_name': 'Charlie',
                'last_name': 'Chen',
                'password': 'password123',
                'roles': {
                    'inventory_api': ['warehouse_manager', 'stock_adjuster', 'movement_approver', 'count_supervisor'],
                    'cielo_website': ['cloud_architect']  # Can design cloud infrastructure
                },
                'attributes': {
                    'global': {
                        'department': 'Operations',
                        'warehouse_ids': [1],  # us-east-1 only
                        'product_categories': ['compute', 'storage'],
                        'max_adjustment_value': 5000,
                        'movement_types': ['migration', 'decommission', 'reallocation'],
                        'can_export_data': False
                    },
                    'cielo_website': {
                        'cloud_providers': ['aws', 'azure'],
                        'cost_center_ids': [1000],
                        'max_resource_cost': 50000,
                        'can_provision_resources': True
                    }
                }
            },
            'david': {
                'email': 'david@example.com',
                'first_name': 'David',
                'last_name': 'Davis',
                'password': 'password123',
                'roles': {
                    'billing_api': ['invoice_viewer', 'payment_viewer'],
                    'inventory_api': ['product_viewer', 'stock_viewer']
                },
                'attributes': {
                    'global': {
                        'department': 'Support',
                        'customer_ids': [100],
                        'warehouse_ids': [],
                        'invoice_limit': 0,
                        'can_export_data': False
                    }
                }
            }
        }

        # Get or create admin user for granting roles
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin123')
        admin_user.save()

        with transaction.atomic():
            for username, config in demo_users.items():
                # Handle reset option
                if options['reset']:
                    try:
                        user = User.objects.get(username=username)
                        UserRole.objects.filter(user=user).delete()
                        UserAttribute.objects.filter(user=user).delete()
                        user.delete()
                        self.stdout.write(f'Deleted existing user: {username}')
                    except User.DoesNotExist:
                        pass

                # Create or get user
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': config['email'],
                        'first_name': config['first_name'],
                        'last_name': config['last_name']
                    }
                )
                
                if created or options['reset']:
                    user.set_password(config['password'])
                    user.save()
                    self.stdout.write(f'Created user: {username}')
                else:
                    self.stdout.write(f'User already exists: {username}')

                # Assign roles
                for service_name, role_names in config['roles'].items():
                    try:
                        service = Service.objects.get(name=service_name)
                        
                        for role_name in role_names:
                            try:
                                role = Role.objects.get(service=service, name=role_name)
                                
                                # Check if role already assigned
                                if not UserRole.objects.filter(user=user, role=role).exists():
                                    RBACService.assign_role(
                                        user=user,
                                        role=role,
                                        granted_by=admin_user,
                                        resource_id=None  # Global roles for demo
                                    )
                                    self.stdout.write(f'  Granted role: {service_name}/{role_name}')
                                else:
                                    self.stdout.write(f'  Role already granted: {service_name}/{role_name}')
                                    
                            except Role.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'  Role not found: {service_name}/{role_name}')
                                )
                                
                    except Service.DoesNotExist:
                        if options['skip_missing_services']:
                            self.stdout.write(
                                self.style.WARNING(f'  Service not found: {service_name} - skipping')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'  Service not found: {service_name}')
                            )

                # Set attributes
                for scope, attributes in config['attributes'].items():
                    try:
                        service = None if scope == 'global' else Service.objects.get(name=scope)
                    except Service.DoesNotExist:
                        if options['skip_missing_services']:
                            self.stdout.write(
                                self.style.WARNING(f'  Service not found for attributes: {scope} - skipping')
                            )
                            continue
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'  Service not found for attributes: {scope}')
                            )
                            continue
                    
                    for attr_name, attr_value in attributes.items():
                        AttributeService.set_user_attribute(
                            user=user,
                            name=attr_name,
                            value=attr_value,
                            service=service,
                            updated_by=admin_user
                        )
                        self.stdout.write(f'  Set attribute: {attr_name} = {attr_value}')

                # Populate Redis cache for all services
                for service in Service.objects.all():
                    try:
                        RedisService.populate_user_attributes(user.id, service.name)
                        self.stdout.write(f'  Populated Redis cache for {service.name}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  Failed to populate Redis for {service.name}: {e}')
                        )

        # Show summary of what services are missing
        registered_services = set(Service.objects.values_list('name', flat=True))
        expected_services = {'billing_api', 'inventory_api', 'identity_provider', 'cielo_website'}
        missing_services = expected_services - registered_services
        
        # Count total expected vs assigned roles
        total_expected_roles = 0
        total_assigned_roles = 0
        for user_config in demo_users.values():
            for service_roles in user_config['roles'].values():
                total_expected_roles += len(service_roles)
        
        demo_usernames = list(demo_users.keys())
        total_assigned_roles = UserRole.objects.filter(
            user__username__in=demo_usernames
        ).count()
        
        if missing_services:
            self.stdout.write(
                self.style.WARNING(f'\nWarning: Some services have not registered yet: {", ".join(missing_services)}')
            )
            self.stdout.write(f'Roles assigned: {total_assigned_roles}/{total_expected_roles}')
            self.stdout.write('Run "python manage.py complete_demo_setup" after all services are up to assign remaining roles.')

        self.stdout.write(self.style.SUCCESS('\nDemo users setup complete!'))
        self.stdout.write('\nUsers created:')
        self.stdout.write('- alice (password: password123) - Senior Manager')
        self.stdout.write('- bob (password: password123) - Billing Specialist')
        self.stdout.write('- charlie (password: password123) - Cloud Infrastructure Manager')
        self.stdout.write('- david (password: password123) - Customer Service Representative')
        self.stdout.write('- admin (password: admin123) - System Administrator')