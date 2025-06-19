# VF Services RBAC-ABAC Library

A flexible, high-performance authorization library combining Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) for Django microservices.

## Features

- 🚀 **High Performance**: Redis-backed attribute caching with sub-millisecond lookups
- 🔐 **Flexible Authorization**: Combine roles and attributes for fine-grained control
- 🎯 **Database-Level Filtering**: Efficient queryset filtering at the SQL level
- 🔌 **DRF Integration**: Drop-in permission classes for Django REST Framework
- 📦 **Pluggable Policies**: Decorator-based policy registration system
- 🔄 **Real-time Updates**: Pub/Sub cache invalidation for immediate permission changes
- 🧪 **Fully Tested**: Comprehensive test suite with mocking support

## Installation

The library is included in the VF Services monorepo. To use it in a service:

```python
# In your service's views.py or models.py
from common.rbac_abac import (
    ABACModelMixin, ABACManager, ABACPermission,
    register_policy, get_user_attributes
)
```

## Quick Start

### 1. Define a Model with ABAC

```python
from django.db import models
from common.rbac_abac import ABACModelMixin, ABACManager

class Invoice(ABACModelMixin, models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    department = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    is_draft = models.BooleanField(default=True)
    
    # Define which policies apply to which actions
    ABAC_POLICIES = {
        'view': 'ownership_or_department',
        'edit': 'ownership_check',
        'approve': 'department_manager',
        'delete': 'admin_only'
    }
    
    # Use the ABAC-aware manager
    objects = ABACManager()
```

### 2. Create Custom Policies

```python
from common.rbac_abac import register_policy

@register_policy('department_manager')
def department_manager(user_attrs, obj=None, action=None):
    """Allow department managers to approve invoices in their department."""
    if not obj or not hasattr(obj, 'department'):
        return False
    
    # Check if user is a manager in the same department
    if user_attrs.department == obj.department:
        return 'manager' in user_attrs.roles or 'department_head' in user_attrs.roles
    
    return False

@register_policy('ownership_or_department')
def ownership_or_department(user_attrs, obj=None, action=None):
    """Allow access if user owns the object or is in the same department."""
    if not obj:
        return False
        
    # Owner check
    if hasattr(obj, 'owner_id') and obj.owner_id == user_attrs.user_id:
        return True
        
    # Department check
    if hasattr(obj, 'department') and obj.department == user_attrs.department:
        return True
        
    return False
```

### 3. Use in ViewSets

```python
from rest_framework.viewsets import ModelViewSet
from common.rbac_abac import ABACPermission

class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    permission_classes = [ABACPermission]
    service_name = 'billing_api'  # Your service name
    
    def get_queryset(self):
        # Automatically filter to only show invoices the user can view
        user_attrs = get_user_attributes(self.request.user.id, self.service_name)
        return Invoice.objects.abac_filter(user_attrs, 'view')
```

## Core Components

### Policy Registry

The policy registry allows you to define reusable authorization rules:

```python
from common.rbac_abac import register_policy, get_policy, list_policies

# Register a policy
@register_policy('my_policy')
def my_policy(user_attrs, obj=None, action=None):
    # Your authorization logic
    return True

# Get a policy by name
policy_func = get_policy('my_policy')

# List all registered policies
all_policies = list_policies()
```

### Model Mixin

The `ABACModelMixin` adds authorization capabilities to your models:

```python
# Check if a user can perform an action
invoice = Invoice.objects.get(pk=1)
user_attrs = get_user_attributes(user.id, 'billing_api')

if invoice.check_abac(user_attrs, 'approve'):
    # User can approve this invoice
    invoice.approve()

# Get all allowed actions for a user
allowed_actions = invoice.get_allowed_actions(user_attrs)
# Returns: ['view', 'edit']  # Based on user's permissions
```

### QuerySet Filtering

Efficient database-level filtering based on permissions:

```python
# Get all invoices the user can view
viewable_invoices = Invoice.objects.abac_filter(user_attrs, 'view')

# Convenience methods
editable_invoices = Invoice.objects.editable_by(user_attrs)
deletable_invoices = Invoice.objects.deletable_by(user_attrs)
```

### DRF Permissions

Drop-in permission classes for Django REST Framework:

```python
from common.rbac_abac import ABACPermission, RoleRequired, ServicePermission

# Object-level ABAC checks
class MyViewSet(ModelViewSet):
    permission_classes = [ABACPermission]
    
# Require specific roles
@api_view(['POST'])
@permission_classes([RoleRequired('admin', 'manager')])
def admin_action(request):
    # Only admins or managers can access
    pass

# Auto-detect service from context
class MyViewSet(ModelViewSet):
    permission_classes = [ServicePermission]  # Auto-detects service name
```

## User Attributes

User attributes are stored in Redis and include:

```python
UserAttributes(
    user_id=123,
    username='john.doe',
    email='john@example.com',
    roles=['editor', 'reviewer'],  # Service-specific roles
    department='Engineering',       # Common attributes
    admin_group_ids=[1, 2, 3],     # Groups where user is admin
    customer_ids=[10, 20],         # Accessible customers
    service_specific_attrs={       # Any service-specific data
        'security_clearance': 'secret',
        'region': 'us-east-1'
    }
)
```

## Built-in Policies

The library includes many common authorization patterns:

- `ownership_check`: User owns the object
- `ownership_or_admin`: Owner or admin role
- `department_match`: Same department as object
- `group_membership`: Member of object's group
- `public_access`: Object is publicly accessible
- `authenticated_only`: Any authenticated user
- `admin_only`: Only admin users
- `read_only`: Only read actions allowed
- `customer_access`: Access to specific customers

## Advanced Usage

### Composite Policies

Combine multiple policies:

```python
from common.rbac_abac.policies import create_composite_policy

# Create an OR combination
create_composite_policy(
    'owner_or_customer_access',
    'ownership_check',
    'customer_access',
    require_all=False  # OR logic
)

# Create an AND combination
create_composite_policy(
    'admin_in_department',
    'admin_only',
    'department_match',
    require_all=True  # AND logic
)
```

### Custom QuerySet Filters

Add database-level filters for your policies:

```python
class MyModel(ABACModelMixin, models.Model):
    # ... fields ...
    
    @classmethod
    def _abac_filter_my_custom_policy(cls, user_attrs):
        """Return a Q object for database filtering."""
        return Q(
            owner_id=user_attrs.user_id
        ) | Q(
            shared_with__contains=user_attrs.email
        )
```

### Performance Optimization

```python
# Prefetch related data for ABAC checks
invoices = Invoice.objects.abac_filter(user_attrs, 'view').abac_prefetch(user_attrs, 'view')

# Batch load attributes for multiple users
for user_id in user_ids:
    RedisService.populate_user_attributes(user_id, 'billing_api')
```

## Testing

### Testing Policies

```python
from common.rbac_abac.models import UserAttributes

def test_department_policy():
    # Create test attributes
    user_attrs = UserAttributes(
        user_id=1,
        username='testuser',
        email='test@example.com',
        department='Sales',
        roles=['manager']
    )
    
    # Create test object
    invoice = Mock(department='Sales')
    
    # Test the policy
    assert department_match(user_attrs, invoice) == True
```

### Testing with Mocked Redis

```python
from unittest.mock import patch

@patch('common.rbac_abac.redis_client.RedisAttributeClient')
def test_with_mocked_redis(mock_redis_class):
    mock_redis = mock_redis_class.return_value
    mock_redis.get_user_attributes.return_value = UserAttributes(
        user_id=1,
        username='test',
        email='test@example.com',
        roles=['admin']
    )
    
    # Your test code here
```

## Configuration

### Django Settings

```python
# Redis configuration
REDIS_HOST = 'redis'
REDIS_PORT = 6379

# Service name (for automatic detection)
SERVICE_NAME = 'billing_api'

# Cache TTL (seconds)
RBAC_CACHE_TTL = 300
```

### Environment Variables

```bash
REDIS_HOST=redis
REDIS_PORT=6379
```

## Troubleshooting

### Common Issues

1. **"No attributes found for user"**
   - Check Redis connectivity
   - Ensure user has roles assigned in Identity Provider
   - Verify service name matches registration

2. **"Policy not found in registry"**
   - Ensure policy module is imported
   - Check for typos in policy name
   - Verify policy is registered with decorator

3. **Slow query performance**
   - Implement database-level filter for the policy
   - Use `select_related()` for foreign keys
   - Check database indexes

### Debug Logging

Enable debug logging to see authorization decisions:

```python
import logging

logging.getLogger('common.rbac_abac').setLevel(logging.DEBUG)
```

## License

This library is part of the VF Services project and follows the same license terms.