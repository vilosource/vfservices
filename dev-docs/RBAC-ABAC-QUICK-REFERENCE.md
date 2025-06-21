# RBAC-ABAC Quick Reference

## 🚀 5-Minute Setup

### 1. Create Service Manifest
```python
# myservice/manifest.py
SERVICE_MANIFEST = {
    "service": {
        "name": "myservice_api",
        "display_name": "My Service"
    },
    "roles": [
        {"name": "myservice_admin", "display_name": "Admin"},
        {"name": "myservice_user", "display_name": "User"}
    ],
    "attributes": [
        {"name": "department", "type": "string"},
        {"name": "level", "type": "integer"}
    ]
}
```

### 2. Register on Startup
```python
# myservice/apps.py
class MyServiceConfig(AppConfig):
    name = 'myservice'
    
    def ready(self):
        from . import policies  # Import to register
        self._register_manifest()
    
    def _register_manifest(self):
        from .manifest import SERVICE_MANIFEST
        requests.post(
            f"{settings.IDENTITY_PROVIDER_URL}/api/services/register/",
            json=SERVICE_MANIFEST
        )
```

### 3. Add to Model
```python
# myservice/models.py
from common.rbac_abac import ABACModelMixin, ABACManager

class MyModel(ABACModelMixin, models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    
    ABAC_POLICIES = {
        'view': 'ownership_or_public',
        'edit': 'ownership_check',
        'delete': 'admin_only'
    }
    
    objects = ABACManager()
```

### 4. Create Policy
```python
# myservice/policies.py
from common.rbac_abac import register_policy

@register_policy('ownership_or_public')
def ownership_or_public(user_attrs, obj=None, action=None):
    if not obj:
        return False
    if obj.is_public:
        return True
    return obj.owner_id == user_attrs.user_id
```

### 5. Protect Views
```python
# myservice/views.py
from common.rbac_abac import ABACPermission

class MyModelViewSet(ModelViewSet):
    permission_classes = [ABACPermission]
    
    def get_queryset(self):
        user_attrs = get_user_attributes(
            self.request.user.id,
            'myservice_api'
        )
        return MyModel.objects.abac_filter(user_attrs, 'view')
```

## 📋 Common Patterns

### Check Role
```python
from common.rbac_abac import RoleRequired

@api_view(['GET'])
@permission_classes([RoleRequired('myservice_admin')])
def admin_only_view(request):
    return Response({"status": "admin access"})
```

### Get User Attributes
```python
from common.rbac_abac.utils import get_user_attributes

user_attrs = get_user_attributes(request.user.id, 'myservice_api')
if 'admin' in user_attrs.roles:
    # Admin logic
```

### Filter Queryset
```python
# Get viewable objects
queryset = MyModel.objects.viewable_by(user_attrs)

# Custom action
queryset = MyModel.objects.abac_filter(user_attrs, 'custom_action')
```

### Check Single Object
```python
obj = MyModel.objects.get(pk=1)
if obj.check_abac(user_attrs, 'edit'):
    # User can edit
```

## 🔧 Built-in Policies

| Policy | Description | Parameters |
|--------|-------------|------------|
| `always_allow` | Always returns True | - |
| `always_deny` | Always returns False | - |
| `authenticated_only` | User must be authenticated | user_attrs |
| `ownership_check` | User owns the object | obj.owner_id |
| `admin_only` | User has admin role | user_attrs.roles |
| `department_match` | Same department | obj.department |
| `group_membership` | User in object's group | obj.allowed_groups |
| `public_read_authenticated_write` | Public view, auth edit | action |
| `role_or_owner` | Has role or owns object | obj, roles |
| `time_based_access` | Time window check | obj.access_times |

## 🛠️ Settings

```python
# settings.py
# Redis Cache
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
REDIS_PORT = 6379
REDIS_DB = 0

# Identity Provider
IDENTITY_PROVIDER_URL = 'http://identity-provider:8000'

# Service Name (must match manifest)
SERVICE_NAME = 'myservice_api'

# Cache TTL (seconds)
RBAC_CACHE_TTL = 300
```

## 🐛 Debugging

### Check User Permissions
```python
# In Django shell
from common.rbac_abac.utils import get_user_attributes
attrs = get_user_attributes(user_id=1, service='myservice_api')
print(f"Roles: {attrs.roles}")
print(f"Department: {attrs.department}")
```

### Test Policy
```python
from myservice.policies import my_policy
from common.rbac_abac.models import UserAttributes

attrs = UserAttributes(user_id=1, roles=['admin'])
result = my_policy(attrs, obj, 'view')
print(f"Policy result: {result}")
```

### View Cache
```python
from common.rbac_abac.redis_client import RedisClient
client = RedisClient()
cached = client.get_user_attributes(user_id=1, service='myservice_api')
print(f"Cached attributes: {cached}")
```

## ❌ Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| 403 Forbidden | Service not registered | Check apps.py registration |
| AttributeError: 'AnonymousUser' | No JWT auth | Add JWT middleware |
| Policy not found | Not imported | Import policies in apps.py |
| Redis connection error | Redis down | Check Redis container |
| No attributes | Cache miss | Refresh cache or check identity provider |

## 📚 Full Documentation
See [RBAC-ABAC-DEVELOPER-GUIDE.md](./RBAC-ABAC-DEVELOPER-GUIDE.md) for complete documentation.