"""
Django management command to set up admin test user with identity_admin role
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from identity_app.models import Service, Role, UserRole


class Command(BaseCommand):
    help = 'Create admin test user with identity_admin role'

    def handle(self, *args, **options):
        # Ensure identity_provider service exists
        service, created = Service.objects.get_or_create(
            name='identity_provider',
            defaults={
                'display_name': 'Identity Provider',
                'description': 'Core identity and authentication service',
                'version': '1.0.0'
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created identity_provider service'))
        
        # Ensure identity_admin role exists
        role, created = Role.objects.get_or_create(
            name='identity_admin',
            service=service,
            defaults={
                'display_name': 'Identity Administrator',
                'description': 'Full access to user and role management via admin API',
                'is_global': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Created identity_admin role'))
        
        # Create or update admin user
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_active': True,
                'is_staff': True
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user'))
        else:
            # Update password in case it's different
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Updated admin user password'))
        
        # Assign identity_admin role if not already assigned
        user_role, created = UserRole.objects.get_or_create(
            user=admin_user,
            role=role,
            defaults={
                'assigned_by': admin_user
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS('Assigned identity_admin role to admin user'))
        else:
            self.stdout.write(self.style.SUCCESS('Admin user already has identity_admin role'))
        
        # Create regular test user for permission testing
        test_user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'testuser@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            self.stdout.write(self.style.SUCCESS('Created test user'))
        
        self.stdout.write(self.style.SUCCESS(
            '\nSetup complete!\n'
            'Admin user: admin / admin123\n'
            'Test user: testuser / testpass123'
        ))