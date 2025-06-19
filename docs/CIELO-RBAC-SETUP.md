# CIELO RBAC Setup Guide

This guide explains how to set up CIELO (Cloud Infrastructure Excellence and Lifecycle Operations) with the RBAC-ABAC system.

## Overview

CIELO has been integrated into the VF Services RBAC-ABAC system as a registered service. This allows fine-grained role-based access control using the same mechanism as other services (billing_api, inventory_api).

## CIELO Roles

The following roles are defined for CIELO:

1. **cielo_admin** - Full administrative access to CIELO platform
2. **cielo_user** - Standard access to CIELO cloud management features  
3. **cielo_viewer** - Read-only access to CIELO dashboards and reports
4. **cloud_architect** - Can design and modify cloud infrastructure
5. **cost_analyst** - Can view and analyze cloud costs and optimization opportunities

## CIELO Attributes

Users can have the following attributes for CIELO:

- **cloud_providers** - List of cloud providers the user can manage (aws, azure, gcp)
- **cost_center_ids** - List of cost center IDs the user can access
- **max_resource_cost** - Maximum monthly cost for resources the user can provision
- **can_provision_resources** - Whether the user can create new cloud resources

## Setup Steps

### 1. Register CIELO Service

First, register the CIELO service with the identity provider:

```bash
# From the host machine
docker exec -it vfservices-cielo_website-1 python manage.py register_service

# Or if running locally
cd cielo_website
python manage.py register_service
```

This will:
- Register CIELO as a service in the identity provider
- Create all CIELO roles
- Define CIELO-specific attributes

### 2. Assign CIELO Roles to Users

Update the demo users to include CIELO roles:

```bash
# From the host machine  
docker exec -it vfservices-identity-provider-1 python manage.py setup_demo_users --skip-missing-services

# Or if running locally
cd identity-provider
python manage.py setup_demo_users --skip-missing-services
```

This assigns:
- **alice** - `cielo_admin` role (full access)
- **bob** - `cost_analyst` role (can analyze costs)
- **charlie** - `cloud_architect` role (can design infrastructure)

### 3. Verify Setup

Run the Playwright tests to verify CIELO access:

```bash
# Test CIELO login
pytest playwright/cielo-website/smoke-tests/test_cielo_index.py::test_cielo_full_login_logout_flow -v
```

### 4. Manual Role Assignment

To manually assign CIELO roles to a user:

```python
# Django shell in identity-provider
from django.contrib.auth.models import User
from identity_app.models import Service, Role
from identity_app.services import RBACService

# Get user and service
user = User.objects.get(username='alice')
service = Service.objects.get(name='cielo_website')
role = Role.objects.get(service=service, name='cielo_admin')

# Assign role
admin_user = User.objects.get(username='admin')
RBACService.assign_role(
    user=user,
    role=role,
    granted_by=admin_user
)

# Populate Redis cache
from identity_app.services import RedisService
RedisService.populate_user_attributes(user.id, 'cielo_website')
```

## How It Works

1. **Middleware Check**: The `CieloAccessMiddleware` checks if authenticated users have any CIELO roles
2. **Redis Lookup**: User roles are fetched from Redis cache via `get_user_attributes()`
3. **Role Validation**: If user has any of the allowed CIELO roles, access is granted
4. **Redirect**: Users without CIELO roles are redirected to the main VF Services site

## Troubleshooting

### User Still Can't Access CIELO

1. **Check if service is registered**:
   ```bash
   docker exec -it vfservices-identity-provider-1 python manage.py shell
   >>> from identity_app.models import Service
   >>> Service.objects.filter(name='cielo_website').exists()
   ```

2. **Check user's roles**:
   ```bash
   docker exec -it vfservices-identity-provider-1 python manage.py shell
   >>> from django.contrib.auth.models import User
   >>> from identity_app.models import UserRole
   >>> user = User.objects.get(username='alice')
   >>> UserRole.objects.filter(user=user, role__service__name='cielo_website').values_list('role__name', flat=True)
   ```

3. **Check Redis cache**:
   ```bash
   docker exec -it vfservices-redis-1 redis-cli
   > GET user:2:attrs:cielo_website
   ```

4. **Force cache refresh**:
   ```python
   from identity_app.services import RedisService
   RedisService.populate_user_attributes(user.id, 'cielo_website')
   ```

### Service Registration Fails

- Ensure identity provider is running
- Check network connectivity between services
- Verify the manifest is valid JSON

## Integration with Existing RBAC-ABAC

CIELO follows the same patterns as other services:

1. **Service Manifest**: Defined in `cielo_website/webapp/manifest.py`
2. **Role Checking**: Uses `common.rbac_abac.redis_client.get_user_attributes()`
3. **Attribute Storage**: User attributes stored in Redis with TTL
4. **Cache Invalidation**: Automatic via signals when roles change

This ensures CIELO access control is consistent with the rest of the VF Services platform.