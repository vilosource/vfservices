from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from identity_app.models import Service, Role, UserRole
from identity_app.services import RedisService, AttributeService


class Command(BaseCommand):
    help = 'Setup Azure Costs roles for demo users'

    def handle(self, *args, **options):
        self.stdout.write("Setting up Azure Costs roles for demo users...")
        
        # Get azure_costs service
        try:
            service = Service.objects.get(name='azure_costs')
            self.stdout.write(f"Found azure_costs service: {service}")
        except Service.DoesNotExist:
            self.stdout.write(self.style.ERROR("Error: azure_costs service not found. Make sure the service is registered."))
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
                self.stdout.write(f"\nProcessing user: {username}")
                
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
                            self.stdout.write(f"  ✓ Granted role: {role_name}")
                        else:
                            self.stdout.write(f"  → Already has role: {role_name}")
                    except Role.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"  ✗ Role not found: {role_name}"))
                
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
                        self.stdout.write(f"  ✓ Set attribute: {attr_name} = {attr_value}")
                
                # Populate Redis cache
                RedisService.populate_user_attributes(user.id, service.name)
                self.stdout.write(f"  ✓ Populated Redis cache")
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"\n✗ User not found: {username}"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Azure costs roles setup complete!"))