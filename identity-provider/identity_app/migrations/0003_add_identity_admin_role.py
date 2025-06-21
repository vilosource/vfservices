# Generated migration for adding identity_admin role

from django.db import migrations


def create_identity_admin_role(apps, schema_editor):
    """Create the identity_admin role"""
    Role = apps.get_model('identity_app', 'Role')
    Service = apps.get_model('identity_app', 'Service')
    
    # Get or create identity provider service
    service, created = Service.objects.get_or_create(
        name='identity_provider',
        defaults={
            'display_name': 'Identity Provider',
            'description': 'Core identity and authentication service',
            'manifest_version': '1.0'
        }
    )
    
    # Create identity_admin role
    Role.objects.get_or_create(
        name='identity_admin',
        service=service,
        defaults={
            'display_name': 'Identity Administrator',
            'description': 'Full access to user and role management via admin API',
            'is_global': True
        }
    )


def remove_identity_admin_role(apps, schema_editor):
    """Remove the identity_admin role"""
    Role = apps.get_model('identity_app', 'Role')
    Service = apps.get_model('identity_app', 'Service')
    
    try:
        service = Service.objects.get(name='identity_provider')
        Role.objects.filter(name='identity_admin', service=service).delete()
    except Service.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('identity_app', '0002_populate_redis_service'),
    ]

    operations = [
        migrations.RunPython(
            create_identity_admin_role,
            remove_identity_admin_role
        ),
    ]