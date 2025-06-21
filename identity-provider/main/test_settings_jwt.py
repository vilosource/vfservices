"""
Test settings for identity provider with JWT authentication support.
"""
from .test_settings import *

# Override middleware to ensure JWT middleware is active
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',  # JWT middleware
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add test authentication backend
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# JWT settings for testing
JWT_AUTH = {
    'JWT_SECRET_KEY': 'test-secret-key-for-testing-only',
    'JWT_ALGORITHM': 'HS256',
    'JWT_EXPIRATION_DELTA': 3600,  # 1 hour
}

# Disable CSRF for API tests
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# Simplified CORS for testing
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://testserver",
]

# Cookie settings for testing
SSO_COOKIE_DOMAIN = None  # Don't set domain for test cookies
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False