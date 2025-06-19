"""
Test configuration for RBAC-ABAC tests
"""

import os
import sys

# Add project root to Python path FIRST
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

# Configure Django settings BEFORE any imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_settings')

import django
from django.conf import settings

# Configure Django settings for tests
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'rest_framework',
        ],
        MIDDLEWARE=[
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
        ],
        SECRET_KEY='test-secret-key',
        USE_TZ=True,
        # Redis settings for tests
        REDIS_HOST='localhost',
        REDIS_PORT=6379,
        # Service name for tests
        SERVICE_NAME='test_service',
        # REST Framework settings
        REST_FRAMEWORK={
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticated',
            ],
        },
    )
    
    # Setup Django
    django.setup()