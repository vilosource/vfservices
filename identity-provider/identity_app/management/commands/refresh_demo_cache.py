"""
Management command to refresh Redis cache for all demo users.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from identity_app.services import RedisService


class Command(BaseCommand):
    help = 'Refresh Redis cache for all demo users'

    def handle(self, *args, **options):
        demo_users = ['alice', 'bob', 'charlie', 'david']
        services = ['billing_api', 'inventory_api', 'identity_provider']
        
        self.stdout.write('Refreshing Redis cache for demo users...\n')
        
        for username in demo_users:
            try:
                user = User.objects.get(username=username)
                self.stdout.write(f'\n{username} (ID: {user.id}):')
                
                for service in services:
                    success = RedisService.populate_user_attributes(user.id, service)
                    status = self.style.SUCCESS('✓') if success else self.style.ERROR('✗')
                    self.stdout.write(f'  {service}: {status}')
                    
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'{username}: User not found'))
                
        self.stdout.write(self.style.SUCCESS('\nRedis cache refresh complete!'))