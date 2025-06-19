"""
Management command to complete demo user setup after all services have registered.
This can be run periodically to ensure all roles are assigned once services are up.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from identity_app.models import Service, Role, UserRole
from identity_app.services import RBACService, RedisService
import time


class Command(BaseCommand):
    help = 'Completes demo user setup by assigning any missing roles after services register'

    def add_arguments(self, parser):
        parser.add_argument(
            '--wait',
            type=int,
            default=0,
            help='Wait up to N seconds for all services to register (0 = no wait)',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Check interval in seconds when waiting',
        )

    def handle(self, *args, **options):
        # Expected services
        expected_services = {'billing_api', 'inventory_api', 'identity_provider'}
        
        # Demo user role mappings
        demo_roles = {
            'alice': {
                'billing_api': ['billing_admin'],
                'inventory_api': ['inventory_manager'],
                'identity_provider': ['customer_manager']
            },
            'bob': {
                'billing_api': ['invoice_manager', 'payment_processor', 'invoice_sender'],
                'inventory_api': ['stock_viewer']
            },
            'charlie': {
                'inventory_api': ['warehouse_manager', 'stock_adjuster', 'movement_approver', 'count_supervisor']
            },
            'david': {
                'billing_api': ['invoice_viewer', 'payment_viewer'],
                'inventory_api': ['product_viewer', 'stock_viewer']
            }
        }
        
        # Wait for services if requested
        if options['wait'] > 0:
            self.stdout.write(f'Waiting up to {options["wait"]} seconds for services to register...')
            start_time = time.time()
            
            while time.time() - start_time < options['wait']:
                registered = set(Service.objects.values_list('name', flat=True))
                missing = expected_services - registered
                
                if not missing:
                    self.stdout.write(self.style.SUCCESS('All services registered!'))
                    break
                    
                self.stdout.write(f'Waiting for: {", ".join(missing)}')
                time.sleep(options['interval'])
            else:
                self.stdout.write(self.style.WARNING('Timeout reached, proceeding with available services'))
        
        # Get admin user for granting roles
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user not found!'))
            return
        
        # Process each demo user
        roles_assigned = 0
        for username, role_map in demo_roles.items():
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'\nProcessing user: {username}')
                
                for service_name, role_names in role_map.items():
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
                                        resource_id=None
                                    )
                                    self.stdout.write(
                                        self.style.SUCCESS(f'  ✓ Granted {service_name}/{role_name}')
                                    )
                                    roles_assigned += 1
                                else:
                                    self.stdout.write(f'  - Already has {service_name}/{role_name}')
                                    
                            except Role.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'  ✗ Role not found: {service_name}/{role_name}')
                                )
                                
                    except Service.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'  ✗ Service not registered: {service_name}')
                        )
                
                # Update Redis cache
                for service in Service.objects.all():
                    try:
                        RedisService.populate_user_attributes(user.id, service.name)
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  Failed to update Redis for {service.name}: {e}')
                        )
                        
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'\nUser not found: {username}'))
        
        # Final summary
        registered_services = set(Service.objects.values_list('name', flat=True))
        missing_services = expected_services - registered_services
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Registered services: {", ".join(sorted(registered_services))}')
        if missing_services:
            self.stdout.write(
                self.style.WARNING(f'Missing services: {", ".join(sorted(missing_services))}')
            )
        self.stdout.write(f'New roles assigned: {roles_assigned}')
        
        if missing_services:
            self.stdout.write(
                self.style.WARNING('\nSome services are still missing. Run this command again later.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\nAll services registered and demo users fully configured!')
            )