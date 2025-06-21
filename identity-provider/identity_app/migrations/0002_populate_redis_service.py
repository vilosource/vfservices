# Generated migration for populating Redis service data

from django.db import migrations


def populate_redis_service(apps, schema_editor):
    """Populate initial Redis service configuration"""
    # This is a placeholder migration for Redis service initialization
    # The actual Redis initialization happens in the service startup
    pass


def reverse_populate_redis_service(apps, schema_editor):
    """Reverse operation - no-op"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('identity_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_redis_service,
            reverse_populate_redis_service
        ),
    ]