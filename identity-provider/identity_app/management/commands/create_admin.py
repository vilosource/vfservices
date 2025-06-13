import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create an admin user if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get admin credentials from environment or use defaults
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@viloforge.com")
        admin_password = os.environ.get("ADMIN_PASSWORD", "admin123")

        self.stdout.write(f"Checking for admin user with username: {admin_username}")
        
        try:
            user = User.objects.get(username=admin_username)
            self.stdout.write(f"Admin user '{admin_username}' already exists")
            
            # Update password to ensure it's correct
            user.set_password(admin_password)
            user.email = admin_email
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            user.save()
            self.stdout.write(f"Updated admin user '{admin_username}' with current settings")
            
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created admin user '{admin_username}'")
            )
            
        # Verify the user configuration
        self.stdout.write(f"Admin user details:")
        self.stdout.write(f"  Username: {user.username}")
        self.stdout.write(f"  Email: {user.email}")
        self.stdout.write(f"  Is superuser: {user.is_superuser}")
        self.stdout.write(f"  Is staff: {user.is_staff}")
        self.stdout.write(f"  Is active: {user.is_active}")
        
        # Test password
        if user.check_password(admin_password):
            self.stdout.write(self.style.SUCCESS("✓ Password verification successful"))
        else:
            self.stdout.write(self.style.ERROR("✗ PASSWORD VERIFICATION FAILED!"))
            
        self.stdout.write(
            self.style.SUCCESS(f"Admin user '{admin_username}' is ready for login")
        )
