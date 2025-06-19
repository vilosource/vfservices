# RBAC-ABAC Quick Start Guide

A condensed guide for developers to quickly integrate RBAC-ABAC into Django APIs.

## 1. Install Dependencies

```bash
pip install django djangorestframework redis PyJWT requests
```

## 2. Copy Common Package

```bash
cp -r /path/to/vfservices/common ./your-project/
```

## 3. Update Settings

```python
# main/settings.py

INSTALLED_APPS = [
    # ... django apps
    'rest_framework',
    'corsheaders',
    'myapp',
]

MIDDLEWARE = [
    # ... other middleware
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',
]

# JWT Config
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret')
JWT_ALGORITHM = 'HS256'

# Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Identity Provider
IDENTITY_PROVIDER_URL = os.environ.get('IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')
RBAC_ABAC_CACHE_TTL = 86400  # 24 hours
```

## 4. Create Service Manifest

```python
# myapp/manifest.py

SERVICE_MANIFEST = {
    "service": {
        "name": "myapp_api",
        "display_name": "MyApp API",
        "description": "My application API"
    },
    "roles": [
        {
            "name": "myapp_admin",
            "display_name": "MyApp Admin",
            "description": "Full admin access",
            "is_global": True
        },
        {
            "name": "myapp_user",
            "display_name": "MyApp User",
            "description": "Regular user access",
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
        }
    ]
}
```

## 5. Register Service on Startup

```python
# myapp/apps.py

from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'

    def ready(self):
        import sys
        if 'runserver' not in sys.argv:
            return
            
        from .manifest import SERVICE_MANIFEST
        from django.conf import settings
        import requests
        
        try:
            response = requests.post(
                f"{settings.IDENTITY_PROVIDER_URL}/api/services/register/",
                json=SERVICE_MANIFEST,
                timeout=10
            )
            if response.status_code == 201:
                logger.info("Service registered successfully")
        except Exception as e:
            logger.error(f"Error registering service: {e}")
```

## 6. Protect Endpoints

### Basic Authentication Check

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_endpoint(request):
    return Response({
        "message": "Authenticated access",
        "user": request.user.username
    })
```

### Role-Based Access

```python
from common.rbac_abac import RoleRequired

@api_view(['GET'])
@permission_classes([RoleRequired('myapp_admin')])
def admin_only(request):
    return Response({"message": "Admin access granted"})

# Multiple roles (OR logic)
@api_view(['GET'])
@permission_classes([RoleRequired(['myapp_admin', 'myapp_manager'])])
def admin_or_manager(request):
    return Response({"message": "Admin or Manager access"})
```

### Attribute-Based Access

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def attribute_based(request):
    user_attrs = getattr(request, 'user_attrs', None)
    
    if not user_attrs:
        return Response({"error": "No attributes"}, status=403)
    
    # Check department
    if user_attrs.department != 'Engineering':
        return Response({"error": "Engineering only"}, status=403)
    
    return Response({"message": "Engineering access granted"})
```

## 7. ViewSet Example

```python
from rest_framework import viewsets
from common.rbac_abac import RoleRequired

class MyModelViewSet(viewsets.ModelViewSet):
    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [RoleRequired('myapp_admin')]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user_attrs = getattr(self.request, 'user_attrs', None)
        
        # Filter based on user attributes
        if 'myapp_admin' in user_attrs.roles:
            return MyModel.objects.all()
        
        # Regular users see only their department's data
        return MyModel.objects.filter(
            department=user_attrs.department
        )
```

## 8. Testing with curl

```bash
# 1. Get token from identity provider
TOKEN=$(curl -s -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}' \
  | jq -r '.token')

# 2. Access protected endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/protected/

# 3. Test role-based endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8001/api/admin-only/
```

## 9. Debug User Permissions

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_user(request):
    """Check current user's permissions."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    return Response({
        "username": request.user.username,
        "roles": user_attrs.roles if user_attrs else [],
        "attributes": user_attrs.__dict__ if user_attrs else {},
        "has_attrs": user_attrs is not None
    })
```

## 10. Common Patterns

### Check Multiple Permissions

```python
def has_budget_approval_permission(request, amount):
    """Check if user can approve budget."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    if not user_attrs:
        return False
    
    # Admin can approve any amount
    if 'myapp_admin' in user_attrs.roles:
        return True
    
    # Manager can approve up to their limit
    if 'myapp_manager' in user_attrs.roles:
        max_budget = getattr(user_attrs, 'max_budget', 0)
        return amount <= max_budget
    
    return False
```

### Filter Data by Attributes

```python
def get_filtered_projects(request):
    """Get projects based on user attributes."""
    user_attrs = getattr(request, 'user_attrs', None)
    
    if not user_attrs:
        return Project.objects.none()
    
    # Admin sees all
    if 'myapp_admin' in user_attrs.roles:
        return Project.objects.all()
    
    # Filter by assigned projects
    project_ids = getattr(user_attrs, 'project_ids', [])
    return Project.objects.filter(id__in=project_ids)
```

### Custom Permission Class

```python
from rest_framework.permissions import BasePermission

class DepartmentPermission(BasePermission):
    """Check if user belongs to specific department."""
    
    def __init__(self, allowed_departments):
        self.allowed_departments = allowed_departments
    
    def has_permission(self, request, view):
        user_attrs = getattr(request, 'user_attrs', None)
        if not user_attrs:
            return False
        
        return user_attrs.department in self.allowed_departments

# Usage
@api_view(['GET'])
@permission_classes([DepartmentPermission(['Engineering', 'IT'])])
def tech_only_endpoint(request):
    return Response({"message": "Tech department access"})
```

## Environment Variables

```env
# .env file
JWT_SECRET_KEY=your-jwt-secret-key
REDIS_HOST=redis
REDIS_PORT=6379
IDENTITY_PROVIDER_URL=http://identity-provider:8000
RBAC_ABAC_CACHE_TTL=86400
```

## Docker Compose

```yaml
services:
  myapp-api:
    build: .
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_HOST=redis
      - IDENTITY_PROVIDER_URL=http://identity-provider:8000
    depends_on:
      - redis
      - identity-provider
    ports:
      - "8003:8000"
```

## Troubleshooting

### No user attributes (403 errors)
```bash
# Refresh Redis cache
docker exec identity-provider python manage.py refresh_demo_cache
```

### Check Redis connection
```python
from common.rbac_abac import get_redis_client
client = get_redis_client()
client.client.ping()  # Should return True
```

### View current user's cached attributes
```python
from common.rbac_abac import get_user_attributes
attrs = get_user_attributes(user_id=1, service_name='myapp_api')
print(attrs.__dict__ if attrs else "No attributes cached")
```

## Next Steps

1. Read the full [Developer Guide](DEVELOPER-GUIDE-RBAC-ABAC.md)
2. Check [example implementations](../billing-api/) in existing services
3. Test with the [demo users](RBAC-ABAC-DEMO-USERS.md)
4. Use the [demo playground](https://vfservices.viloforge.com/demo/playground/) to test