# RBAC-ABAC Implementation Documentation

## Overview

This document describes the implemented Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) system for VF Services. The system provides fine-grained, scalable authorization across microservices while maintaining service autonomy.

For demonstration purposes, see:
- [RBAC-ABAC Demo Users Guide](./RBAC-ABAC-DEMO-USERS.md) - Four pre-configured users (Alice, Bob, Charlie, David) showcasing different access patterns
- [RBAC-ABAC Demo Pages Guide](./RBAC-ABAC-DEMO-PAGES.md) - Interactive web interface for testing and exploring the RBAC-ABAC system

## Architecture

### Core Components

#### 1. Redis Cache Layer
- **Purpose**: Fast, distributed cache for user attributes and roles
- **Implementation**: Redis 7-alpine with persistent storage
- **Features**:
  - Namespaced storage by service: `user:{user_id}:attrs:{service_name}`
  - Pub/Sub for real-time cache invalidation
  - Configurable TTL (default: 300 seconds)

#### 2. Shared RBAC-ABAC Library (`common/rbac_abac/`)

##### Policy Registry (`registry.py`)
- Decorator-based policy registration: `@register_policy('policy_name')`
- Global `POLICY_REGISTRY` for policy storage
- Policy listing and retrieval functions
- Automatic error handling (secure default: deny)

##### Model Integration (`mixins.py`)
- `ABACModelMixin`: Template Method pattern for Django models
- `check_abac(user_attrs, action)`: Main permission check method
- `get_allowed_actions(user_attrs)`: Lists permitted actions
- Metaclass validation for proper configuration

##### Database Filtering (`querysets.py`)
- `ABACQuerySet`: Custom QuerySet with `abac_filter()` method
- Database-level filtering for common policies
- Python-level fallback for complex policies
- `ABACManager`: Convenience methods (`viewable_by`, `editable_by`)

##### DRF Permissions (`permissions.py`)
- `ABACPermission`: Object-level permission checks
- `RoleRequired`: Simple role-based checks
- `ServicePermission`: Auto-detects service from context
- `CombinedPermission`: Complex permission logic with AND/OR

##### Redis Client (`redis_client.py`)
- `RedisAttributeClient`: Manages Redis operations
- `UserAttributes` model: Data structure for user information
- Pub/Sub support for cache invalidation
- Health check and connection management

##### Default Policies (`policies.py`)
Comprehensive set of pre-built policies:
- **Ownership**: `ownership_check`, `ownership_or_admin`
- **Department**: `department_match`, `department_match_or_admin`
- **Groups**: `group_membership`, `owner_or_group_admin`
- **Access**: `public_access`, `authenticated_only`, `admin_only`
- **Service**: `service_admin`, `customer_access`, `document_access`
- **Utility**: `read_only`, `deny_all`

#### 3. Identity Provider Extensions

##### Django Models (`identity_app/models.py`)
- `Service`: Registered microservices with manifest tracking
- `Role`: Service-namespaced roles (global or resource-scoped)
- `UserRole`: User-role assignments with expiration support
- `ServiceAttribute`: Service-declared attribute definitions
- `UserAttribute`: User attribute values (global or service-specific)
- `ServiceManifest`: Versioned service configuration

##### Services Layer (`identity_app/services.py`)
- `RBACService`: Role management (assign, revoke, query)
- `AttributeService`: Attribute management (get, set)
- `RedisService`: Cache population and invalidation
- `ManifestService`: Service registration handling

##### Signal Handlers (`identity_app/signals.py`)
Automatic cache updates on:
- UserRole creation/update/deletion
- UserAttribute changes
- Service activation/deactivation
- User detail modifications

## Usage Guide

### 1. Defining Models with ABAC

```python
from django.db import models
from common.rbac_abac import ABACModelMixin, ABACManager

class Document(ABACModelMixin, models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=50)
    is_public = models.BooleanField(default=False)
    
    # Define ABAC policies for actions
    ABAC_POLICIES = {
        'view': 'ownership_or_admin',
        'edit': 'department_match',
        'delete': 'admin_only'
    }
    
    # Use ABACManager for filtering
    objects = ABACManager()
```

### 2. Creating Custom Policies

```python
from common.rbac_abac import register_policy

@register_policy('custom_policy')
def custom_policy(user_attrs, obj=None, action=None):
    """Custom authorization logic."""
    if obj is None:
        return False
    
    # Example: Check multiple conditions
    if user_attrs.department == obj.department:
        return True
    if 'supervisor' in user_attrs.roles:
        return True
    
    return False
```

### 3. Using in Views/ViewSets

```python
from rest_framework.viewsets import ModelViewSet
from common.rbac_abac import ABACPermission

class DocumentViewSet(ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [ABACPermission]
    service_name = 'document_service'  # Required for Redis lookup
    
    def get_queryset(self):
        # Filter queryset based on user permissions
        user_attrs = get_user_attributes(self.request.user.id, self.service_name)
        return Document.objects.abac_filter(user_attrs, 'view')
```

### 4. Service Manifest Format

```json
{
  "service": "billing_api",
  "display_name": "Billing API",
  "description": "Handles invoicing and payments",
  "version": "1.0",
  "roles": [
    {
      "name": "billing_admin",
      "display_name": "Billing Administrator",
      "description": "Full access to billing functions",
      "is_global": true
    },
    {
      "name": "invoice_viewer",
      "display_name": "Invoice Viewer",
      "description": "Can view invoices",
      "is_global": false
    }
  ],
  "attributes": [
    {
      "name": "department",
      "display_name": "Department",
      "description": "User's department",
      "type": "string",
      "required": true,
      "default": "General"
    },
    {
      "name": "customer_ids",
      "display_name": "Accessible Customers",
      "description": "List of customer IDs user can access",
      "type": "list_integer",
      "required": false
    }
  ]
}
```

## Security Considerations

### Secure Defaults
- All policies return `False` (deny) on error
- Missing policies result in access denial
- Invalid user attributes block access
- Expired roles are automatically excluded

### Redis Security
- Use strong Redis passwords in production
- Enable Redis ACLs for fine-grained access control
- Use TLS for Redis connections
- Monitor Redis memory usage

### Policy Best Practices
- Keep policies simple and testable
- Use descriptive policy names
- Document policy logic
- Regularly audit policy usage
- Test policies with various edge cases

## Performance Optimization

### Database Query Optimization
- Use `select_related()` and `prefetch_related()` in managers
- Implement database filters for common policies
- Limit Python-level filtering to complex cases

### Redis Optimization
- Set appropriate TTLs based on data volatility
- Use pipeline operations for bulk updates
- Monitor cache hit rates
- Implement local in-memory caching for hot data

### Bulk Operations
- Use `abac_filter()` for list endpoints
- Batch Redis operations when possible
- Implement pagination for large result sets

## Monitoring and Debugging

### Interactive Demo Interface
The website service provides comprehensive demo pages for real-time monitoring and testing:
- **Demo Dashboard** (`/demo/`): System status and user switching
- **RBAC Dashboard** (`/demo/rbac/`): Live permission data from Redis
- **API Explorer** (`/demo/api/`): Test endpoints with different users
- **Permission Matrix** (`/demo/matrix/`): Visual role assignments
- **Access Playground** (`/demo/playground/`): Pre-configured test scenarios

See the [Demo Pages Guide](./RBAC-ABAC-DEMO-PAGES.md) for detailed usage instructions.

### Management Commands
```bash
# Refresh Redis cache for all demo users
python manage.py refresh_demo_cache

# Setup demo users with roles and attributes
python manage.py setup_demo_users

# Complete full demo setup
python manage.py complete_demo_setup
```

### Logging
The system logs key events:
- Policy execution (DEBUG level)
- Cache operations (DEBUG level)
- Role/attribute changes (INFO level)
- Errors and denials (WARNING/ERROR level)

### Health Checks
- Redis connection: `RedisAttributeClient.health_check()`
- Policy registry: `list_policies()`
- Service status: Check `Service.is_active`
- Demo setup: Check dashboard at `/demo/`

### Common Issues

1. **"No attributes found for user"**
   - Ensure user has roles assigned
   - Check Redis connectivity
   - Verify service name matches

2. **"Policy not found in registry"**
   - Confirm policy is registered
   - Check for typos in policy name
   - Ensure policies module is imported

3. **Stale permissions**
   - Check Redis TTL settings
   - Verify signals are connected
   - Monitor pub/sub messages

## Testing

### Unit Testing Policies
```python
from common.rbac_abac.models import UserAttributes

def test_custom_policy():
    user_attrs = UserAttributes(
        user_id=1,
        username='testuser',
        email='test@example.com',
        department='Engineering',
        roles=['developer']
    )
    
    obj = Mock(department='Engineering')
    assert custom_policy(user_attrs, obj) == True
```

### Integration Testing
```python
class TestDocumentAccess(TestCase):
    def test_user_can_view_own_documents(self):
        user = User.objects.create_user('testuser')
        doc = Document.objects.create(owner=user)
        
        # Populate Redis
        RedisService.populate_user_attributes(user.id, 'test_service')
        
        # Test access
        user_attrs = get_user_attributes(user.id, 'test_service')
        self.assertTrue(doc.check_abac(user_attrs, 'view'))
```

## Migration Guide

### Adding ABAC to Existing Models

1. Add `ABACModelMixin` to model inheritance
2. Define `ABAC_POLICIES` mapping
3. Replace manager with `ABACManager`
4. Update views to use `ABACPermission`
5. Test thoroughly before deployment

### Transitioning from Simple Permissions

1. Map existing permissions to policies
2. Create transition policies that check both systems
3. Gradually migrate endpoints
4. Monitor for authorization failures
5. Remove old permission checks

## API Reference

### Registry Functions
- `register_policy(name)`: Decorator to register policies
- `get_policy(name)`: Retrieve a policy function
- `list_policies()`: Get all registered policies

### Model Methods
- `check_abac(user_attrs, action)`: Check permission
- `get_allowed_actions(user_attrs)`: List allowed actions

### QuerySet Methods
- `abac_filter(user_attrs, action)`: Filter by permissions
- `viewable_by(user_attrs)`: Shortcut for view filtering
- `editable_by(user_attrs)`: Shortcut for edit filtering

### Service Functions
- `RBACService.assign_role()`: Assign role to user
- `AttributeService.set_user_attribute()`: Set attribute
- `RedisService.populate_user_attributes()`: Populate cache
- `ManifestService.register_manifest()`: Register service

## Appendix: Design Decisions

### Why Redis?
- Sub-millisecond latency for attribute lookups
- Built-in pub/sub for cache invalidation
- Proven reliability at scale
- Simple key-value model fits our needs

### Why Decorator-Based Policies?
- Clear, discoverable policy definitions
- Easy testing in isolation
- No magic strings in business logic
- Supports dynamic policy loading

### Why Service Manifests?
- Services self-describe their needs
- No central configuration changes
- Supports dynamic service discovery
- Enables automated documentation