# Developer Guide: Building Django APIs with RBAC-ABAC

This guide will walk you through creating Django API projects that integrate with the VF Services RBAC-ABAC (Role-Based Access Control with Attribute-Based Access Control) system.

## Table of Contents
1. [Overview](#overview)
2. [Project Setup](#project-setup)
3. [Installing RBAC-ABAC Package](#installing-rbac-abac-package)
4. [Configuration](#configuration)
5. [Creating Your Service Manifest](#creating-your-service-manifest)
6. [Implementing Authentication](#implementing-authentication)
7. [Defining Roles and Permissions](#defining-roles-and-permissions)
8. [Protecting API Endpoints](#protecting-api-endpoints)
9. [Working with User Attributes](#working-with-user-attributes)
10. [Testing Your Implementation](#testing-your-implementation)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Overview

The RBAC-ABAC system provides centralized authentication and authorization for microservices. It combines:
- **RBAC**: Role-based permissions (e.g., "billing_admin", "inventory_manager")
- **ABAC**: Attribute-based permissions (e.g., department, customer_ids, warehouse_ids)

### Architecture
```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────┐
│   Your Django   │────▶│ Identity Provider │────▶│    Redis    │
│   API Service   │     │    (Central)      │     │   (Cache)   │
└─────────────────┘     └──────────────────┘     └─────────────┘
         │                        │
         └────────────────────────┘
           JWT Token Validation
```

## Project Setup

### 1. Create a New Django Project

```bash
# Create project directory
mkdir my-api-service
cd my-api-service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Django and dependencies
pip install django djangorestframework django-cors-headers redis PyJWT requests
```

### 2. Start Django Project

```bash
django-admin startproject main .
python manage.py startapp myapp
```

### 3. Project Structure

```
my-api-service/
├── main/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── myapp/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── manifest.py      # Service manifest
│   ├── models.py
│   ├── policies.py      # ABAC policies
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
├── common/              # Shared RBAC-ABAC package
│   ├── __init__.py
│   ├── jwt_auth/
│   └── rbac_abac/
├── manage.py
└── requirements.txt
```

## Installing RBAC-ABAC Package

### 1. Copy the Common Package

Copy the `common` directory from the VF Services repository to your project:

```bash
cp -r /path/to/vfservices/common ./
```

### 2. Update Requirements

Create `requirements.txt`:

```txt
Django>=4.2
djangorestframework>=3.14
django-cors-headers>=4.0
redis>=4.5
PyJWT>=2.8
requests>=2.31
python-decouple>=3.8
structlog>=23.1
```

## Configuration

### 1. Update Django Settings

Edit `main/settings.py`:

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-jwt-secret')
JWT_ALGORITHM = 'HS256'

# Applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'myapp',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',  # JWT Auth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'myapp_db'),
        'USER': os.environ.get('POSTGRES_USER', 'myapp_user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'myapp_pass'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
    }
}

# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

# RBAC-ABAC Configuration
RBAC_ABAC_CACHE_TTL = int(os.environ.get('RBAC_ABAC_CACHE_TTL', 86400))  # 24 hours
IDENTITY_PROVIDER_URL = os.environ.get('IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'myapp': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 2. Environment Variables

Create `.env` file:

```env
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
POSTGRES_DB=myapp_db
POSTGRES_USER=myapp_user
POSTGRES_PASSWORD=myapp_pass
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Identity Provider
IDENTITY_PROVIDER_URL=http://identity-provider:8000
RBAC_ABAC_CACHE_TTL=86400
```

## Creating Your Service Manifest

Create `myapp/manifest.py`:

```python
"""
Service manifest for MyApp API.
This defines the roles and attributes supported by this service.
"""

SERVICE_MANIFEST = {
    "service": {
        "name": "myapp_api",
        "display_name": "MyApp API",
        "description": "My application API service with RBAC-ABAC"
    },
    "roles": [
        {
            "name": "myapp_admin",
            "display_name": "MyApp Administrator",
            "description": "Full administrative access to MyApp",
            "is_global": True
        },
        {
            "name": "myapp_manager",
            "display_name": "MyApp Manager",
            "description": "Can manage resources and approve actions",
            "is_global": False
        },
        {
            "name": "myapp_user",
            "display_name": "MyApp User",
            "description": "Basic user access to MyApp",
            "is_global": False
        },
        {
            "name": "myapp_viewer",
            "display_name": "MyApp Viewer",
            "description": "Read-only access to MyApp",
            "is_global": False
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department",
            "attribute_type": "string",
            "is_required": False
        },
        {
            "name": "project_ids",
            "display_name": "Project IDs",
            "description": "List of project IDs the user can access",
            "attribute_type": "list_integer",
            "is_required": False,
            "default_value": []
        },
        {
            "name": "max_budget",
            "display_name": "Maximum Budget",
            "description": "Maximum budget the user can approve",
            "attribute_type": "integer",
            "is_required": False,
            "default_value": 0
        },
        {
            "name": "can_export_data",
            "display_name": "Can Export Data",
            "description": "Whether the user can export data",
            "attribute_type": "boolean",
            "is_required": False,
            "default_value": False
        }
    ]
}
```

## Implementing Authentication

### 1. Register Service on Startup

Edit `myapp/apps.py`:

```python
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        """Register service with identity provider on startup."""
        # Only run in main process, not in migrations or shell
        import sys
        if 'runserver' not in sys.argv and 'gunicorn' not in sys.argv:
            return
            
        from .manifest import SERVICE_MANIFEST
        from django.conf import settings
        import requests
        
        try:
            # Register with identity provider
            response = requests.post(
                f"{settings.IDENTITY_PROVIDER_URL}/api/services/register/",
                json=SERVICE_MANIFEST,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.info(f"Service registered successfully: {response.json()}")
            else:
                logger.error(f"Failed to register service: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error registering service: {e}")
```

### 2. Create Login View (Optional)

If your service needs its own login endpoint:

```python
# myapp/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import requests


class ProxyLoginView(APIView):
    """Proxy login requests to identity provider."""
    permission_classes = []
    
    def post(self, request):
        try:
            # Forward to identity provider
            response = requests.post(
                f"{settings.IDENTITY_PROVIDER_URL}/api/login/",
                json=request.data
            )
            
            if response.status_code == 200:
                return Response(response.json())
            else:
                return Response(
                    {"error": "Authentication failed"},
                    status=response.status_code
                )
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
```

## Defining Roles and Permissions

### 1. Create Views with Role Requirements

```python
# myapp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.rbac_abac import RoleRequired, get_user_attributes
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def public_endpoint(request):
    """Any authenticated user can access this."""
    return Response({
        "message": "This is a public endpoint",
        "user": request.user.username,
        "timestamp": timezone.now()
    })


@api_view(['GET'])
@permission_classes([RoleRequired('myapp_admin')])
def admin_only_endpoint(request):
    """Only users with myapp_admin role can access this."""
    return Response({
        "message": "Admin access granted",
        "user": request.user.username,
        "role": "myapp_admin",
        "timestamp": timezone.now()
    })


@api_view(['GET'])
@permission_classes([RoleRequired(['myapp_manager', 'myapp_admin'])])
def manager_endpoint(request):
    """Users with either myapp_manager OR myapp_admin role can access."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    return Response({
        "message": "Manager access granted",
        "user": request.user.username,
        "roles": user_attrs.roles if user_attrs else [],
        "department": user_attrs.department if user_attrs else None,
        "timestamp": timezone.now()
    })
```

### 2. Create ViewSets with Permissions

```python
# myapp/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Project
from .serializers import ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """ViewSet for managing projects."""
    serializer_class = ProjectSerializer
    
    def get_permissions(self):
        """Different permissions for different actions."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Only managers and admins can modify
            return [RoleRequired(['myapp_manager', 'myapp_admin'])]
        else:
            # All authenticated users can view
            return [IsAuthenticated()]
    
    def get_queryset(self):
        """Filter projects based on user attributes."""
        user = self.request.user
        user_attrs = getattr(self.request, 'user_attrs', None)
        
        if not user_attrs:
            return Project.objects.none()
        
        # Admins see all projects
        if 'myapp_admin' in user_attrs.roles:
            return Project.objects.all()
        
        # Others see only their assigned projects
        if hasattr(user_attrs, 'project_ids') and user_attrs.project_ids:
            return Project.objects.filter(id__in=user_attrs.project_ids)
        
        return Project.objects.none()
    
    @action(detail=True, methods=['post'], 
            permission_classes=[RoleRequired('myapp_manager')])
    def approve(self, request, pk=None):
        """Approve a project (managers only)."""
        project = self.get_object()
        user_attrs = getattr(request, 'user_attrs', None)
        
        # Check budget limit
        if hasattr(user_attrs, 'max_budget'):
            if project.budget > user_attrs.max_budget:
                return Response(
                    {"error": f"Budget exceeds your limit of {user_attrs.max_budget}"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        project.approved = True
        project.approved_by = request.user
        project.approved_at = timezone.now()
        project.save()
        
        return Response({"status": "approved"})
```

## Working with User Attributes

### 1. Define ABAC Policies

Create `myapp/policies.py`:

```python
"""
ABAC policies for MyApp.
These define attribute-based access rules.
"""
from common.rbac_abac import register_policy
from typing import Any, Dict


@register_policy('project.view')
def can_view_project(user_attrs: Dict[str, Any], resource: Any) -> bool:
    """Check if user can view a specific project."""
    # Admins can view all
    if 'myapp_admin' in user_attrs.get('roles', []):
        return True
    
    # Check if project ID is in user's allowed projects
    project_ids = user_attrs.get('project_ids', [])
    return resource.id in project_ids


@register_policy('project.approve')
def can_approve_project(user_attrs: Dict[str, Any], resource: Any) -> bool:
    """Check if user can approve a project."""
    # Must have manager role
    if 'myapp_manager' not in user_attrs.get('roles', []):
        return False
    
    # Check budget limit
    max_budget = user_attrs.get('max_budget', 0)
    if resource.budget > max_budget:
        return False
    
    # Check department match
    user_dept = user_attrs.get('department')
    if user_dept and hasattr(resource, 'department'):
        return user_dept == resource.department
    
    return True


@register_policy('data.export')
def can_export_data(user_attrs: Dict[str, Any], resource: Any = None) -> bool:
    """Check if user can export data."""
    return user_attrs.get('can_export_data', False)
```

### 2. Use Policies in Views

```python
# myapp/views.py
from common.rbac_abac import get_policy


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """Export data endpoint with ABAC check."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    if not user_attrs:
        return Response(
            {"error": "User attributes not found"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check export permission using policy
    can_export = get_policy('data.export')
    if not can_export(user_attrs.__dict__):
        return Response(
            {"error": "You don't have permission to export data"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Perform export...
    return Response({"status": "Export started"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_project(request, project_id):
    """Approve a project with ABAC checks."""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return Response(
            {"error": "Project not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    
    user_attrs = getattr(request, 'user_attrs', None)
    if not user_attrs:
        return Response(
            {"error": "User attributes not found"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check approval permission using policy
    can_approve = get_policy('project.approve')
    if not can_approve(user_attrs.__dict__, project):
        return Response(
            {"error": "You don't have permission to approve this project"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Approve the project
    project.approved = True
    project.save()
    
    return Response({"status": "Project approved"})
```

## Testing Your Implementation

### 1. Create Test Cases

```python
# myapp/tests.py
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from unittest.mock import patch, MagicMock
from common.rbac_abac.models import UserAttributes


class RBACTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def get_auth_token(self):
        """Mock getting a JWT token."""
        return "mock-jwt-token"
    
    @patch('common.rbac_abac.get_user_attributes')
    def test_admin_access(self, mock_get_attrs):
        """Test admin role access."""
        # Mock user attributes with admin role
        mock_attrs = UserAttributes(
            user_id=self.user.id,
            username=self.user.username,
            email='test@example.com',
            roles=['myapp_admin'],
            department='IT',
            customer_ids=[],
            service_specific_attrs={}
        )
        mock_get_attrs.return_value = mock_attrs
        
        # Set authorization header
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.get_auth_token()}'
        )
        
        # Test admin endpoint
        response = self.client.get('/api/admin-only/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Admin access granted', response.data['message'])
    
    @patch('common.rbac_abac.get_user_attributes')
    def test_insufficient_permissions(self, mock_get_attrs):
        """Test access denial for insufficient permissions."""
        # Mock user attributes with only viewer role
        mock_attrs = UserAttributes(
            user_id=self.user.id,
            username=self.user.username,
            email='test@example.com',
            roles=['myapp_viewer'],
            department='Sales',
            customer_ids=[],
            service_specific_attrs={}
        )
        mock_get_attrs.return_value = mock_attrs
        
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {self.get_auth_token()}'
        )
        
        # Test admin endpoint - should be denied
        response = self.client.get('/api/admin-only/')
        self.assertEqual(response.status_code, 403)
```

### 2. Integration Testing

Create a test script:

```python
# test_integration.py
import requests
import json

# Configuration
BASE_URL = "http://localhost:8000"
IDENTITY_URL = "http://localhost:8001"

# Test user credentials
TEST_USERS = {
    "admin": {"username": "admin_user", "password": "admin123"},
    "manager": {"username": "manager_user", "password": "manager123"},
    "viewer": {"username": "viewer_user", "password": "viewer123"}
}


def test_rbac_flow():
    """Test complete RBAC flow."""
    
    for role, creds in TEST_USERS.items():
        print(f"\nTesting {role} user...")
        
        # 1. Login
        login_resp = requests.post(
            f"{IDENTITY_URL}/api/login/",
            json=creds
        )
        
        if login_resp.status_code != 200:
            print(f"  ❌ Login failed: {login_resp.status_code}")
            continue
        
        token = login_resp.json()['token']
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Test endpoints
        endpoints = [
            ("/api/public/", "Public endpoint"),
            ("/api/admin-only/", "Admin endpoint"),
            ("/api/manager/", "Manager endpoint"),
        ]
        
        for endpoint, name in endpoints:
            resp = requests.get(
                f"{BASE_URL}{endpoint}",
                headers=headers
            )
            
            status_icon = "✅" if resp.status_code == 200 else "❌"
            print(f"  {status_icon} {name}: {resp.status_code}")


if __name__ == "__main__":
    test_rbac_flow()
```

## Best Practices

### 1. Security
- **Never** expose internal service URLs to external clients
- Always validate JWT tokens
- Use HTTPS in production
- Rotate JWT secrets regularly
- Implement rate limiting

### 2. Performance
- Cache user attributes in Redis (already handled by RBAC-ABAC)
- Use database indexes for filtered queries
- Implement pagination for list endpoints
- Use select_related/prefetch_related for ORM queries

### 3. Error Handling
```python
from rest_framework.exceptions import PermissionDenied


def safe_get_user_attrs(request):
    """Safely get user attributes with error handling."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    if not user_attrs:
        logger.warning(f"No user attributes for {request.user}")
        raise PermissionDenied("User attributes not found")
    
    return user_attrs
```

### 4. Logging
```python
import structlog

logger = structlog.get_logger()


@api_view(['POST'])
@permission_classes([RoleRequired('myapp_admin')])
def sensitive_action(request):
    """Log sensitive actions for audit."""
    user_attrs = safe_get_user_attrs(request)
    
    logger.info(
        "sensitive_action_performed",
        user_id=request.user.id,
        username=request.user.username,
        roles=user_attrs.roles,
        action="sensitive_action",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Perform action...
    return Response({"status": "success"})
```

### 5. Documentation
```python
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


@swagger_auto_schema(
    operation_description="Admin only endpoint",
    responses={
        200: "Success",
        403: "Forbidden - requires myapp_admin role",
        401: "Unauthorized - invalid token"
    },
    manual_parameters=[
        openapi.Parameter(
            'Authorization',
            openapi.IN_HEADER,
            description="JWT token",
            type=openapi.TYPE_STRING,
            required=True,
            default="Bearer <token>"
        )
    ]
)
@api_view(['GET'])
@permission_classes([RoleRequired('myapp_admin')])
def documented_endpoint(request):
    """Well-documented endpoint."""
    return Response({"message": "Success"})
```

## Troubleshooting

### Common Issues and Solutions

#### 1. 403 Forbidden Errors
```python
# Check user attributes
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_permissions(request):
    """Debug endpoint to check user permissions."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    return Response({
        "user": request.user.username,
        "has_attrs": user_attrs is not None,
        "roles": user_attrs.roles if user_attrs else [],
        "attributes": user_attrs.__dict__ if user_attrs else {}
    })
```

#### 2. Redis Connection Issues
```python
# Add Redis health check
@api_view(['GET'])
def health_check(request):
    """Health check with Redis status."""
    from common.rbac_abac import get_redis_client
    
    try:
        client = get_redis_client()
        client.client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return Response({
        "service": "myapp_api",
        "status": "healthy",
        "redis": redis_status
    })
```

#### 3. Service Registration Failures
```python
# Manual service registration endpoint
@api_view(['POST'])
@permission_classes([RoleRequired('myapp_admin')])
def register_service(request):
    """Manually register service with identity provider."""
    from .manifest import SERVICE_MANIFEST
    
    try:
        response = requests.post(
            f"{settings.IDENTITY_PROVIDER_URL}/api/services/register/",
            json=SERVICE_MANIFEST
        )
        
        return Response({
            "status": "registered" if response.status_code == 201 else "failed",
            "response": response.json()
        })
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
```

## Deployment Considerations

### 1. Docker Configuration

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations and start server
CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
```

### 2. Docker Compose Integration

Add to `docker-compose.yml`:

```yaml
services:
  myapp-api:
    build: ./my-api-service
    container_name: myapp-api
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - POSTGRES_HOST=postgres
      - REDIS_HOST=redis
      - IDENTITY_PROVIDER_URL=http://identity-provider:8000
    depends_on:
      - postgres
      - redis
      - identity-provider
    ports:
      - "8003:8000"
    networks:
      - vfservices-network
```

### 3. Production Settings

```python
# Production overrides
if not DEBUG:
    # Security
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Performance
    CONN_MAX_AGE = 60
    
    # Caching
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/1',
        }
    }
```

## Summary

This guide covered:
1. Setting up a Django API project with RBAC-ABAC
2. Creating service manifests and registering with identity provider
3. Implementing role-based and attribute-based access control
4. Testing and troubleshooting
5. Best practices and deployment

The RBAC-ABAC system provides a powerful, centralized way to manage authentication and authorization across microservices while maintaining flexibility for service-specific requirements.