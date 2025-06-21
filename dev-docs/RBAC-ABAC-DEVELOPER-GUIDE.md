# RBAC-ABAC Developer Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Implementation Guide](#implementation-guide)
6. [API Reference](#api-reference)
7. [Best Practices](#best-practices)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

## Overview

The VF Services RBAC-ABAC system is a hybrid authorization framework that combines Role-Based Access Control (RBAC) with Attribute-Based Access Control (ABAC). This provides both simple role checks and complex policy-based permissions across microservices.

### Key Features
- **Service Autonomy**: Each service defines its own roles and attributes
- **Redis Caching**: High-performance user attribute storage
- **Policy-Based**: Declarative authorization policies
- **Django/DRF Integration**: Seamless integration with Django models and REST framework
- **Cross-Service Auth**: JWT-based authentication with shared attributes

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Client App    │────▶│  CIELO Website  │────▶│  Identity       │
│                 │ JWT │                 │     │  Provider       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                │                         │
                                │ JWT Cookie              │ Register
                                ▼                         │ Services
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Azure Costs    │────▶│   Redis Cache   │◀────│  Service        │
│  API            │     │ (User Attrs)    │     │  Manifests      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Component Overview

1. **Identity Provider**: Central authority for users, roles, and attributes
2. **Service Manifests**: Service self-registration with roles/attributes
3. **Redis Cache**: Performance layer for user attributes
4. **JWT Tokens**: Cross-service authentication with user_id
5. **Policy Engine**: Evaluates ABAC policies for authorization

## Quick Start

### 1. Install Dependencies

```python
# In your service's requirements.txt
Django==4.2.7
djangorestframework==3.14.0
redis==5.0.1
PyJWT==2.8.0
```

### 2. Add RBAC-ABAC to Your Service

```python
# myservice/apps.py
from django.apps import AppConfig
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

class MyServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myservice'

    def ready(self):
        # Import policies to register them
        from . import policies
        
        # Register service manifest
        self._register_manifest()
    
    def _register_manifest(self):
        from .manifest import SERVICE_MANIFEST
        
        try:
            response = requests.post(
                f"{settings.IDENTITY_PROVIDER_URL}/api/services/register/",
                json=SERVICE_MANIFEST,
                timeout=10
            )
            if response.status_code == 201:
                logger.info(f"Successfully registered {self.name} service")
        except Exception as e:
            logger.error(f"Failed to register service: {e}")
```

### 3. Define Your Service Manifest

```python
# myservice/manifest.py
SERVICE_MANIFEST = {
    "service": {
        "name": "myservice_api",
        "display_name": "My Service API",
        "description": "Service for managing resources",
        "version": "1.0.0"
    },
    "roles": [
        {
            "name": "myservice_admin",
            "display_name": "My Service Admin",
            "description": "Full administrative access",
            "is_global": True
        },
        {
            "name": "myservice_user",
            "display_name": "My Service User",
            "description": "Standard user access",
            "is_global": False
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department",
            "type": "string",
            "required": False
        },
        {
            "name": "clearance_level",
            "display_name": "Clearance Level",
            "description": "Security clearance (1-5)",
            "type": "integer",
            "required": False,
            "default": 1
        }
    ]
}
```

### 4. Create a Protected Model

```python
# myservice/models.py
from django.db import models
from django.contrib.auth.models import User
from common.rbac_abac import ABACModelMixin, ABACManager

class SecureDocument(ABACModelMixin, models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    clearance_required = models.IntegerField(default=1)
    department = models.CharField(max_length=50, null=True, blank=True)
    
    # Define ABAC policies for each action
    ABAC_POLICIES = {
        'view': 'clearance_and_department_check',
        'edit': 'ownership_or_admin',
        'delete': 'ownership_check',
        'share': 'admin_only'
    }
    
    objects = ABACManager()
    
    class Meta:
        db_table = 'myservice_documents'
```

### 5. Implement Custom Policies

```python
# myservice/policies.py
from common.rbac_abac import register_policy

@register_policy('clearance_and_department_check')
def clearance_and_department_check(user_attrs, obj=None, action=None):
    """Check if user has required clearance and department match."""
    if not obj:
        return False
    
    # Check clearance level
    user_clearance = getattr(user_attrs, 'clearance_level', 1)
    if user_clearance < obj.clearance_required:
        return False
    
    # Check department if specified
    if obj.department:
        user_dept = getattr(user_attrs, 'department', None)
        if user_dept != obj.department:
            return False
    
    return True

@register_policy('ownership_or_admin')
def ownership_or_admin(user_attrs, obj=None, action=None):
    """Allow if user owns the object or is an admin."""
    if not obj:
        return False
    
    # Check if admin
    if 'myservice_admin' in getattr(user_attrs, 'roles', []):
        return True
    
    # Check ownership
    if hasattr(obj, 'owner_id'):
        return obj.owner_id == user_attrs.user_id
    
    return False
```

### 6. Protect Your API Views

```python
# myservice/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from common.rbac_abac import ABACPermission, RoleRequired
from common.rbac_abac.utils import get_user_attributes
from .models import SecureDocument
from .serializers import SecureDocumentSerializer

class SecureDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = SecureDocumentSerializer
    permission_classes = [ABACPermission]
    service_name = 'myservice_api'
    
    def get_queryset(self):
        """Filter documents based on ABAC policies."""
        user_attrs = get_user_attributes(
            self.request.user.id, 
            self.service_name
        )
        return SecureDocument.objects.abac_filter(user_attrs, 'view')
    
    @action(detail=True, methods=['post'])
    @permission_classes([RoleRequired('myservice_admin')])
    def share(self, request, pk=None):
        """Admin-only endpoint to share documents."""
        document = self.get_object()
        # Sharing logic here
        return Response({'status': 'shared'})
```

## Core Concepts

### Roles vs Attributes

**Roles** are predefined sets of permissions:
- Binary: User has role or doesn't
- Service-scoped: `myservice_admin`, `billing_viewer`
- Can be global or service-specific
- Can have expiration dates

**Attributes** are user properties:
- Flexible: Any data type (string, int, list, etc.)
- Context-aware: Department, location, clearance level
- Used in policy decisions
- Cached in Redis for performance

### Policy System

Policies are Python functions that evaluate to True/False:

```python
@register_policy('policy_name')
def policy_name(user_attrs, obj=None, action=None):
    # user_attrs: UserAttributes object with roles and attributes
    # obj: The object being accessed (optional)
    # action: The action being performed (optional)
    return True  # or False
```

### Service Manifests

Service manifests declare a service's authorization requirements:

```python
{
    "service": {
        "name": "unique_service_name",
        "display_name": "Human Readable Name",
        "description": "Service description"
    },
    "roles": [...],      # Service-specific roles
    "attributes": [...]   # Required user attributes
}
```

## Implementation Guide

### Step 1: Planning Your Authorization Model

Before implementing, consider:
1. What roles does your service need?
2. What user attributes affect permissions?
3. What actions can users perform?
4. What are the authorization rules?

### Step 2: Setting Up the Common Library

Copy the `common/rbac_abac` directory to your service:

```bash
cp -r ../identity-provider/common/rbac_abac ./common/
```

### Step 3: Configure Django Settings

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'common.rbac_abac',
    'myservice',
]

# Redis configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)

# Identity Provider URL
IDENTITY_PROVIDER_URL = os.environ.get(
    'IDENTITY_PROVIDER_URL', 
    'http://identity-provider:8000'
)

# Service name (must match manifest)
SERVICE_NAME = 'myservice_api'
```

### Step 4: Create Management Commands

```python
# myservice/management/commands/setup_demo_data.py
from django.core.management.base import BaseCommand
from common.rbac_abac.utils import get_user_attributes
from identity_app.services import RBACService, AttributeService

class Command(BaseCommand):
    help = 'Setup demo users and roles'
    
    def handle(self, *args, **kwargs):
        # Create demo users with roles
        rbac_service = RBACService()
        attr_service = AttributeService()
        
        # Assign roles
        rbac_service.assign_role_to_user(
            user_id=1,
            role_name='myservice_admin',
            service_name='myservice_api'
        )
        
        # Set attributes
        attr_service.set_user_attribute(
            user_id=1,
            attribute_name='department',
            value='Engineering',
            service_name='myservice_api'
        )
```

### Step 5: Testing Your Implementation

```python
# tests/test_rbac.py
from django.test import TestCase
from common.rbac_abac.models import UserAttributes
from myservice.policies import clearance_and_department_check
from myservice.models import SecureDocument

class RBACTestCase(TestCase):
    def test_clearance_policy(self):
        # Create test data
        doc = SecureDocument(clearance_required=3)
        
        # Test with sufficient clearance
        user_attrs = UserAttributes(
            user_id=1,
            clearance_level=5,
            department='Engineering'
        )
        self.assertTrue(
            clearance_and_department_check(user_attrs, doc)
        )
        
        # Test with insufficient clearance
        user_attrs.clearance_level = 1
        self.assertFalse(
            clearance_and_department_check(user_attrs, doc)
        )
```

## API Reference

### Decorators

#### `@register_policy(name)`
Register a policy function in the global registry.

```python
@register_policy('my_policy')
def my_policy(user_attrs, obj=None, action=None):
    return True
```

### Permissions

#### `ABACPermission`
DRF permission class for object-level ABAC checks.

```python
class MyViewSet(ModelViewSet):
    permission_classes = [ABACPermission]
```

#### `RoleRequired(role_name)`
Simple role-based permission check.

```python
@permission_classes([RoleRequired('admin')])
def admin_view(request):
    pass
```

#### `ServicePermission`
Auto-detects service context for permissions.

```python
class MyViewSet(ModelViewSet):
    permission_classes = [ServicePermission]
    service_name = 'myservice_api'
```

### Model Mixins

#### `ABACModelMixin`
Add ABAC support to Django models.

```python
class MyModel(ABACModelMixin, models.Model):
    ABAC_POLICIES = {
        'view': 'policy_name',
        'edit': 'another_policy'
    }
```

### Managers

#### `ABACManager`
Provides ABAC-aware query methods.

```python
# Filter by policy
queryset = MyModel.objects.abac_filter(user_attrs, 'view')

# Convenience methods
viewable = MyModel.objects.viewable_by(user_attrs)
editable = MyModel.objects.editable_by(user_attrs)
```

### Utilities

#### `get_user_attributes(user_id, service_name)`
Retrieve user attributes from Redis cache.

```python
from common.rbac_abac.utils import get_user_attributes

user_attrs = get_user_attributes(
    request.user.id, 
    'myservice_api'
)
```

## Best Practices

### 1. Service Registration

Always register your service on startup:

```python
def ready(self):
    # Don't check DEBUG - register in all environments
    self._register_manifest()
```

### 2. Policy Design

Keep policies simple and testable:

```python
# Good: Single responsibility
@register_policy('is_owner')
def is_owner(user_attrs, obj=None, action=None):
    if not obj or not hasattr(obj, 'owner_id'):
        return False
    return obj.owner_id == user_attrs.user_id

# Bad: Too complex
@register_policy('complex_policy')
def complex_policy(user_attrs, obj=None, action=None):
    # 50 lines of nested if statements...
```

### 3. Performance Optimization

Use database-level filtering when possible:

```python
class OptimizedManager(ABACManager):
    def viewable_by(self, user_attrs):
        # First apply database filters
        qs = self.filter(is_public=True)
        
        # Then apply ABAC filters
        return qs.abac_filter(user_attrs, 'view')
```

### 4. Error Handling

Always handle missing attributes gracefully:

```python
@register_policy('department_check')
def department_check(user_attrs, obj=None, action=None):
    user_dept = getattr(user_attrs, 'department', None)
    if not user_dept:
        return False  # Secure default
    return user_dept == obj.department
```

### 5. Testing Strategy

Test each component in isolation:

```python
# Test policies
def test_policy():
    attrs = UserAttributes(user_id=1, roles=['admin'])
    assert my_policy(attrs, obj) == True

# Test with Redis
def test_with_cache():
    cache_attrs(user_id=1, attrs={'role': 'admin'})
    attrs = get_user_attributes(1, 'service')
    assert 'admin' in attrs.roles
```

## Troubleshooting

### Common Issues

#### 1. 403 Forbidden Errors

**Cause**: Service not registered or user lacks permissions.

**Solution**:
- Check service registration in logs
- Verify user has required roles/attributes
- Use demo dashboard to inspect user permissions

#### 2. Redis Connection Errors

**Cause**: Redis not running or misconfigured.

**Solution**:
```bash
# Check Redis connection
docker compose ps redis
docker compose logs redis

# Test Redis connection
python manage.py shell
>>> from common.rbac_abac.redis_client import RedisClient
>>> client = RedisClient()
>>> client.ping()
```

#### 3. Attributes Not Loading

**Cause**: Missing user_id in JWT or cache miss.

**Solution**:
- Verify JWT contains user_id
- Check Redis for cached attributes
- Manually refresh cache:

```python
from identity_app.services import RedisService
redis_service = RedisService()
redis_service.cache_user_attributes(user_id, service_name)
```

#### 4. Policy Not Found

**Cause**: Policy not registered or import error.

**Solution**:
- Ensure policies.py is imported in apps.py
- Check policy name matches exactly
- Verify no import errors in policies.py

### Debug Tools

#### 1. Demo Dashboard
Access at `/demo/` to:
- View system status
- Switch between users
- Inspect permissions

#### 2. RBAC Dashboard
Access at `/demo/rbac/` to:
- View user roles and attributes
- Test policy evaluation
- Check cache status

#### 3. Management Commands

```bash
# Refresh user cache
python manage.py refresh_demo_cache

# Setup demo users
python manage.py setup_demo_users

# Check service registration
python manage.py list_services
```

#### 4. Logging

Enable debug logging:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'common.rbac_abac': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Examples

### Example 1: Department-Based Access

```python
# models.py
class DepartmentResource(ABACModelMixin, models.Model):
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=50)
    
    ABAC_POLICIES = {
        'view': 'same_department',
        'edit': 'department_manager'
    }

# policies.py
@register_policy('same_department')
def same_department(user_attrs, obj=None, action=None):
    if not obj:
        return False
    user_dept = getattr(user_attrs, 'department', None)
    return user_dept == obj.department

@register_policy('department_manager')
def department_manager(user_attrs, obj=None, action=None):
    if not same_department(user_attrs, obj):
        return False
    return 'manager' in getattr(user_attrs, 'roles', [])
```

### Example 2: Time-Based Access

```python
# policies.py
from datetime import datetime, time

@register_policy('business_hours_only')
def business_hours_only(user_attrs, obj=None, action=None):
    """Allow access only during business hours."""
    now = datetime.now().time()
    start = time(9, 0)  # 9 AM
    end = time(17, 0)   # 5 PM
    
    # Admins can access anytime
    if 'admin' in getattr(user_attrs, 'roles', []):
        return True
    
    return start <= now <= end
```

### Example 3: Multi-Factor Authorization

```python
# policies.py
@register_policy('multi_factor_auth')
def multi_factor_auth(user_attrs, obj=None, action=None):
    """Require multiple conditions for sensitive operations."""
    # Must have role
    if 'sensitive_ops' not in getattr(user_attrs, 'roles', []):
        return False
    
    # Must be in secure location
    location = getattr(user_attrs, 'location', None)
    if location not in ['headquarters', 'secure_facility']:
        return False
    
    # Must have recent authentication
    last_auth = getattr(user_attrs, 'last_authenticated', None)
    if not last_auth:
        return False
    
    from datetime import datetime, timedelta
    auth_time = datetime.fromisoformat(last_auth)
    if datetime.now() - auth_time > timedelta(hours=1):
        return False
    
    return True
```

### Example 4: Hierarchical Permissions

```python
# policies.py
@register_policy('hierarchical_access')
def hierarchical_access(user_attrs, obj=None, action=None):
    """Allow access based on organizational hierarchy."""
    if not obj:
        return False
    
    user_level = getattr(user_attrs, 'org_level', 0)
    obj_level = getattr(obj, 'required_level', 0)
    
    # Higher level users can access lower level resources
    return user_level >= obj_level
```

## Conclusion

The VF Services RBAC-ABAC system provides a powerful, flexible authorization framework that scales with your application's needs. By following this guide and best practices, you can implement secure, maintainable authorization in your services.

For additional support:
- Review the example implementations in existing services
- Check the troubleshooting section for common issues
- Use the demo dashboard for testing and debugging
- Consult the API reference for detailed documentation

Remember: Security is only as strong as its weakest link. Always test your authorization policies thoroughly and follow the principle of least privilege.