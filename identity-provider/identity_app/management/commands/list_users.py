"""
Management command to list all users in the system.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from identity_app.models import UserRole
from django.db.models import Count, Prefetch
# from tabulate import tabulate  # Optional dependency
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'List all users in the system with their roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active users',
        )
        parser.add_argument(
            '--with-roles',
            action='store_true',
            help='Show detailed role information for each user',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['table', 'csv', 'json'],
            default='table',
            help='Output format (default: table)',
        )
        parser.add_argument(
            '--sort',
            type=str,
            choices=['username', 'email', 'date_joined', 'last_login'],
            default='username',
            help='Sort by field (default: username)',
        )

    def handle(self, *args, **options):
        # Build query
        queryset = User.objects.all()
        
        if options['active_only']:
            queryset = queryset.filter(is_active=True)
        
        # Add role count annotation
        queryset = queryset.annotate(role_count=Count('user_roles'))
        
        # Prefetch roles if needed
        if options['with_roles']:
            queryset = queryset.prefetch_related(
                Prefetch('user_roles', 
                        queryset=UserRole.objects.select_related('role__service'))
            )
        
        # Sort
        sort_field = options['sort']
        if sort_field == 'last_login':
            queryset = queryset.order_by(f'-{sort_field}')  # Most recent first
        else:
            queryset = queryset.order_by(sort_field)
        
        users = list(queryset)
        
        if not users:
            self.stdout.write(self.style.WARNING('No users found.'))
            return
        
        if options['format'] == 'json':
            self._output_json(users, options['with_roles'])
        elif options['format'] == 'csv':
            self._output_csv(users, options['with_roles'])
        else:
            self._output_table(users, options['with_roles'])
        
        # Summary
        total_users = len(users)
        active_users = sum(1 for u in users if u.is_active)
        self.stdout.write(
            self.style.SUCCESS(
                f'\nTotal users: {total_users} (Active: {active_users}, Inactive: {total_users - active_users})'
            )
        )

    def _output_table(self, users, with_roles):
        """Output users in table format."""
        # Header
        header_format = "{:<5} {:<15} {:<30} {:<20} {:<7} {:<6} {:<6} {:<6} {:<12} {:<16}"
        self.stdout.write(header_format.format(
            'ID', 'Username', 'Email', 'Name', 'Active', 'Staff', 'Super', 'Roles', 'Created', 'Last Login'
        ))
        self.stdout.write('-' * 120)
        
        # Rows
        row_format = "{:<5} {:<15} {:<30} {:<20} {:<7} {:<6} {:<6} {:<6} {:<12} {:<16}"
        for user in users:
            self.stdout.write(row_format.format(
                user.id,
                user.username[:15],
                user.email[:30],
                (f"{user.first_name} {user.last_name}".strip() or '-')[:20],
                'Yes' if user.is_active else 'No',
                'Yes' if user.is_staff else '-',
                'Yes' if user.is_superuser else '-',
                user.role_count,
                user.date_joined.strftime('%Y-%m-%d'),
                user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
            ))
        
        if with_roles:
            self.stdout.write('\n' + self.style.WARNING('User Roles:'))
            for user in users:
                if user.user_roles.exists():
                    self.stdout.write(f'\n{self.style.SUCCESS(user.username)}:')
                    for ur in user.user_roles.all():
                        self.stdout.write(f"  {ur.role.service.name:<20} {ur.role.name:<25} {ur.role.display_name:<30} {ur.granted_at.strftime('%Y-%m-%d')}")

    def _output_csv(self, users, with_roles):
        """Output users in CSV format."""
        import csv
        import sys
        
        writer = csv.writer(sys.stdout)
        
        # Header
        headers = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'is_active', 'is_staff', 'is_superuser', 'role_count', 
                  'date_joined', 'last_login']
        if with_roles:
            headers.append('roles')
        
        writer.writerow(headers)
        
        # Data
        for user in users:
            row = [
                user.id,
                user.username,
                user.email,
                user.first_name,
                user.last_name,
                user.is_active,
                user.is_staff,
                user.is_superuser,
                user.role_count,
                user.date_joined.isoformat(),
                user.last_login.isoformat() if user.last_login else ''
            ]
            
            if with_roles:
                roles = []
                for ur in user.user_roles.all():
                    roles.append(f"{ur.role.service.name}:{ur.role.name}")
                row.append('|'.join(roles))
            
            writer.writerow(row)

    def _output_json(self, users, with_roles):
        """Output users in JSON format."""
        import json
        
        data = []
        for user in users:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'role_count': user.role_count,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            if with_roles:
                user_data['roles'] = []
                for ur in user.user_roles.all():
                    user_data['roles'].append({
                        'service': ur.role.service.name,
                        'role': ur.role.name,
                        'display_name': ur.role.display_name,
                        'granted_at': ur.granted_at.isoformat()
                    })
            
            data.append(user_data)
        
        self.stdout.write(json.dumps(data, indent=2))