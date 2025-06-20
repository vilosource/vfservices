# Azure Costs Service Configuration Guide

## Overview

This document provides a complete guide for configuring the Azure Costs service to work with the VF Services RBAC-ABAC authentication and authorization system. Following this guide will enable proper cross-service authentication between CIELO and Azure Costs.

## Current Issue

The Azure Costs service is currently not integrated with the RBAC-ABAC system, which causes authentication failures when users try to access Azure Costs API endpoints after logging in through CIELO. The JWT tokens are shared correctly via the `.viloforge.com` domain, but the service doesn't recognize user roles and attributes.

## Required Configuration Steps

### 1. Create Service Manifest

Create a new file `azure_costs/manifest.py` with the service definition:

```python
# azure_costs/manifest.py

SERVICE_MANIFEST = {
    "service": "azure_costs",
    "display_name": "Azure Costs Management",
    "description": "Service for tracking and managing Azure cloud costs, budgets, and resource optimization",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "costs_viewer",
            "display_name": "Costs Viewer",
            "description": "Can view Azure costs, reports, and dashboards",
            "is_global": False
        },
        {
            "name": "costs_analyst",
            "display_name": "Costs Analyst", 
            "description": "Can analyze costs, create reports, and view optimization recommendations",
            "is_global": False
        },
        {
            "name": "costs_manager",
            "display_name": "Costs Manager",
            "description": "Can manage budgets, cost allocations, and configure alerts",
            "is_global": False
        },
        {
            "name": "costs_admin",
            "display_name": "Costs Administrator",
            "description": "Full access to all cost management features including API configuration",
            "is_global": True
        }
    ],
    "attributes": [
        {
            "name": "azure_subscription_ids",
            "display_name": "Azure Subscription IDs",
            "description": "List of Azure subscription IDs the user can access",
            "type": "list_string",
            "is_required": False,
            "default_value": []
        },
        {
            "name": "cost_center_ids",
            "display_name": "Cost Center IDs",
            "description": "List of cost centers the user can view and manage",
            "type": "list_string",
            "is_required": False,
            "default_value": []
        },
        {
            "name": "resource_group_patterns",
            "display_name": "Resource Group Patterns",
            "description": "Regex patterns for resource groups the user can access",
            "type": "list_string",
            "is_required": False,
            "default_value": []
        },
        {
            "name": "budget_limit",
            "display_name": "Budget Limit",
            "description": "Maximum budget amount (in USD) the user can allocate",
            "type": "integer",
            "is_required": False,
            "default_value": 0
        },
        {
            "name": "can_export_reports",
            "display_name": "Can Export Reports",
            "description": "Whether user can export cost reports to CSV/Excel",
            "type": "boolean",
            "is_required": False,
            "default_value": False
        },
        {
            "name": "can_modify_tags",
            "display_name": "Can Modify Tags",
            "description": "Whether user can modify cost allocation tags",
            "type": "boolean",
            "is_required": False,
            "default_value": False
        },
        {
            "name": "max_forecast_months",
            "display_name": "Max Forecast Months",
            "description": "Maximum number of months user can forecast costs",
            "type": "integer",
            "is_required": False,
            "default_value": 3
        }
    ]
}
```

### 2. Update Application Configuration

Update `azure_costs/apps.py` to register the service on startup:

```python
# azure_costs/apps.py

from django.apps import AppConfig
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class AzureCostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'azure_costs'

    def ready(self):
        # Import policies to register them
        try:
            from . import policies
        except ImportError:
            logger.warning("No policies module found")
        
        # Register service manifest with identity provider
        self._register_manifest()
    
    def _register_manifest(self):
        """Register service manifest with identity provider."""
        try:
            from .manifest import SERVICE_MANIFEST
            
            # Skip registration in test environment or if explicitly disabled
            if getattr(settings, 'SKIP_SERVICE_REGISTRATION', False):
                logger.info("Skipping service registration (SKIP_SERVICE_REGISTRATION=True)")
                return
            
            identity_provider_url = getattr(
                settings, 
                'IDENTITY_PROVIDER_URL', 
                'http://identity-provider:8000'
            )
            register_url = f"{identity_provider_url}/api/services/register/"
            
            logger.info(f"Registering Azure Costs service manifest with identity provider at {register_url}")
            
            response = requests.post(
                register_url,
                json=SERVICE_MANIFEST,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.info("Azure Costs service manifest registered successfully")
                data = response.json()
                logger.info(f"Service ID: {data.get('service_id', 'N/A')}")
            elif response.status_code == 409:
                logger.info("Azure Costs service already registered - skipping")
            else:
                logger.error(
                    f"Failed to register Azure Costs service manifest: "
                    f"{response.status_code} - {response.text}"
                )
        
        except ImportError:
            logger.warning("No service manifest found at azure_costs.manifest - skipping registration")
        except requests.exceptions.ConnectionError:
            logger.warning(
                "Could not connect to identity provider - service will retry on next request. "
                "This is normal during initial startup."
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Error registering service manifest: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during manifest registration: {e}")
```

### 3. Create ABAC Policies

Create `azure_costs/policies.py` with authorization policies:

```python
# azure_costs/policies.py

from common.rbac_abac.registry import register_policy
import logging
import re

logger = logging.getLogger(__name__)

@register_policy('azure_costs_view_all')
def view_all_costs_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can view all Azure costs without restrictions."""
    roles = user_attrs.get('roles', [])
    return 'costs_admin' in roles

@register_policy('azure_costs_view_subscription')
def view_subscription_costs_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can view costs for specific subscriptions."""
    roles = user_attrs.get('roles', [])
    user_subscriptions = user_attrs.get('azure_subscription_ids', [])
    
    # Admins can view all subscriptions
    if 'costs_admin' in roles:
        return True
    
    # Other roles need subscription assignment
    if any(role in roles for role in ['costs_manager', 'costs_analyst', 'costs_viewer']):
        if obj and hasattr(obj, 'subscription_id'):
            return obj.subscription_id in user_subscriptions
        return bool(user_subscriptions)
    
    return False

@register_policy('azure_costs_view_cost_center')
def view_cost_center_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can view specific cost center data."""
    roles = user_attrs.get('roles', [])
    user_cost_centers = user_attrs.get('cost_center_ids', [])
    
    # Admins can view all cost centers
    if 'costs_admin' in roles:
        return True
    
    # Check cost center assignment
    if obj and hasattr(obj, 'cost_center_id'):
        return obj.cost_center_id in user_cost_centers
    
    return bool(user_cost_centers)

@register_policy('azure_costs_view_resource_group')
def view_resource_group_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can view specific resource group costs."""
    roles = user_attrs.get('roles', [])
    patterns = user_attrs.get('resource_group_patterns', [])
    
    # Admins can view all resource groups
    if 'costs_admin' in roles:
        return True
    
    # Check resource group patterns
    if obj and hasattr(obj, 'resource_group'):
        for pattern in patterns:
            try:
                if re.match(pattern, obj.resource_group):
                    return True
            except re.error:
                logger.warning(f"Invalid regex pattern: {pattern}")
    
    return False

@register_policy('azure_costs_manage_budgets')
def manage_budgets_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can create or modify budgets."""
    roles = user_attrs.get('roles', [])
    budget_limit = user_attrs.get('budget_limit', 0)
    
    # Only managers and admins can manage budgets
    if 'costs_admin' in roles:
        return True
    
    if 'costs_manager' in roles:
        if obj and hasattr(obj, 'amount'):
            return obj.amount <= budget_limit
        return budget_limit > 0
    
    return False

@register_policy('azure_costs_export_reports')
def export_reports_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can export cost reports."""
    roles = user_attrs.get('roles', [])
    can_export = user_attrs.get('can_export_reports', False)
    
    # Admins always can export
    if 'costs_admin' in roles:
        return True
    
    # Others need explicit permission
    return can_export and any(role in roles for role in ['costs_manager', 'costs_analyst'])

@register_policy('azure_costs_modify_tags')
def modify_tags_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can modify cost allocation tags."""
    roles = user_attrs.get('roles', [])
    can_modify = user_attrs.get('can_modify_tags', False)
    
    # Only admins and managers with permission
    if 'costs_admin' in roles:
        return True
    
    return 'costs_manager' in roles and can_modify

@register_policy('azure_costs_forecast')
def forecast_costs_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can access cost forecasting."""
    roles = user_attrs.get('roles', [])
    max_months = user_attrs.get('max_forecast_months', 0)
    
    # Need analyst role or higher
    allowed_roles = ['costs_admin', 'costs_manager', 'costs_analyst']
    if not any(role in roles for role in allowed_roles):
        return False
    
    # Check forecast period limit
    if obj and hasattr(obj, 'forecast_months'):
        return obj.forecast_months <= max_months
    
    return max_months > 0

@register_policy('azure_costs_api_access')
def api_access_policy(user_attrs, obj=None, action=None):
    """Policy to check if user can access Azure Costs API endpoints."""
    roles = user_attrs.get('roles', [])
    
    # Any costs role grants API access
    allowed_roles = ['costs_admin', 'costs_manager', 'costs_analyst', 'costs_viewer']
    return any(role in roles for role in allowed_roles)
```

### 4. Update Django Settings

Update `main/settings.py`:

```python
# Update INSTALLED_APPS to use the new app config
INSTALLED_APPS = [
    # ... other apps ...
    "azure_costs.apps.AzureCostsConfig",  # Change from just "azure_costs"
    # ... other apps ...
]

# Ensure SERVICE_NAME matches the manifest
SERVICE_NAME = 'azure_costs'

# Identity provider configuration
IDENTITY_PROVIDER_URL = os.environ.get(
    'IDENTITY_PROVIDER_URL',
    'http://identity-provider:8000'
)

# Optional: Skip registration during tests
SKIP_SERVICE_REGISTRATION = os.environ.get('SKIP_SERVICE_REGISTRATION', 'False').lower() == 'true'
```

### 5. Update Views to Use RBAC Permissions

Update the API views to properly check permissions:

```python
# azure_costs/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from common.rbac_abac.permissions import PolicyPermission
from django.utils import timezone

@api_view(['GET'])
@permission_classes([IsAuthenticated, PolicyPermission('azure_costs_api_access')])
def private(request):
    """Private endpoint that requires Azure Costs API access."""
    user_attrs = getattr(request, 'user_attrs', {})
    
    return Response({
        "message": "Azure Costs API - Private Endpoint",
        "service": "azure_costs",
        "user": {
            "id": request.user.id,
            "username": request.user.username,
            "email": getattr(request.user, 'email', None)
        },
        "roles": user_attrs.get('roles', []),
        "permissions": {
            "can_view_all_costs": 'costs_admin' in user_attrs.get('roles', []),
            "can_export_reports": user_attrs.get('can_export_reports', False),
            "can_modify_tags": user_attrs.get('can_modify_tags', False),
            "assigned_subscriptions": user_attrs.get('azure_subscription_ids', []),
            "assigned_cost_centers": user_attrs.get('cost_center_ids', [])
        },
        "timestamp": timezone.now().isoformat()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, PolicyPermission('azure_costs_view_subscription')])
def costs_summary(request):
    """Get cost summary for user's assigned subscriptions."""
    user_attrs = getattr(request, 'user_attrs', {})
    subscriptions = user_attrs.get('azure_subscription_ids', [])
    
    # In a real implementation, this would query actual Azure costs
    return Response({
        "subscriptions": subscriptions,
        "total_cost": 0,
        "currency": "USD",
        "period": "current_month"
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated, PolicyPermission('azure_costs_export_reports')])
def export_report(request):
    """Export cost report endpoint."""
    return Response({
        "export_url": "/api/reports/download/sample.csv",
        "expires_at": (timezone.now() + timezone.timedelta(hours=1)).isoformat()
    })
```

## User Role Assignment

After implementing the configuration, assign roles to users. For the demo users:

### Alice - Costs Administrator
```python
# In identity provider Django shell
from identity_app.services import RBACService
from django.contrib.auth.models import User
from identity_app.models import Service, Role

alice = User.objects.get(username='alice')
service = Service.objects.get(name='azure_costs')
admin_role = Role.objects.get(service=service, name='costs_admin')

RBACService.assign_role(
    user=alice,
    role=admin_role,
    granted_by=User.objects.get(username='admin')
)

# Set attributes
from identity_app.services import AttributeService
AttributeService.set_user_attribute(
    user=alice,
    attribute_name='can_export_reports',
    value=True,
    service=service
)
```

### Bob - Costs Analyst
```python
bob = User.objects.get(username='bob')
analyst_role = Role.objects.get(service=service, name='costs_analyst')

RBACService.assign_role(
    user=bob,
    role=analyst_role,
    granted_by=User.objects.get(username='admin')
)

# Assign specific subscriptions
AttributeService.set_user_attribute(
    user=bob,
    attribute_name='azure_subscription_ids',
    value=['sub-12345', 'sub-67890'],
    service=service
)
```

## Testing the Configuration

### 1. Service Registration Verification

Check the Django logs when Azure Costs starts up:
```
INFO: Registering Azure Costs service manifest with identity provider
INFO: Azure Costs service manifest registered successfully
INFO: Service ID: <uuid>
```

### 2. Manual Testing with curl

```bash
# Get JWT token by logging in
TOKEN=$(curl -X POST https://identity.viloforge.com/api/token/ \
  -d "username=alice&password=password123" | jq -r '.access')

# Test Azure Costs API
curl -H "Authorization: Bearer $TOKEN" \
  https://azure-costs.cielo.viloforge.com/api/private
```

### 3. Playwright Test Verification

After configuration, the integration test should pass:
```bash
cd playwright/cielo-website/integration-tests
python test_azure_costs_access.py
```

Expected output:
```
✓ Successfully logged into CIELO
✓ JWT cookie found
✓ Alice is authorized to access Azure Costs API private endpoint
✅ TEST PASSED: Alice has proper authorization!
```

## Troubleshooting

### Service Not Registered

If you see "Service azure_costs not found" errors:
1. Check that `manifest.py` exists and is valid
2. Verify `apps.py` uses `AzureCostsConfig`
3. Check Django logs for registration errors
4. Manually trigger registration:
   ```python
   from azure_costs.apps import AzureCostsConfig
   app = AzureCostsConfig('azure_costs', __import__('azure_costs'))
   app._register_manifest()
   ```

### Authentication Failures (403)

If users still get 403 errors:
1. Verify user has assigned roles:
   ```python
   from identity_app.models import UserRole
   UserRole.objects.filter(
       user__username='alice',
       role__service__name='azure_costs'
   ).values_list('role__name', flat=True)
   ```

2. Check Redis cache:
   ```bash
   docker exec -it vfservices-redis-1 redis-cli
   > GET user:2:attrs:azure_costs
   ```

3. Force cache refresh:
   ```python
   from identity_app.services import RedisService
   RedisService.populate_user_attributes(alice.id, 'azure_costs')
   ```

### Policy Not Found

If you see "Policy not found in registry" errors:
1. Ensure `policies.py` is imported in `apps.py`
2. Check policy names match exactly
3. List registered policies:
   ```python
   from common.rbac_abac.registry import list_policies
   print([p for p in list_policies() if 'azure_costs' in p])
   ```

## Security Considerations

1. **Principle of Least Privilege**: Assign minimum required roles
2. **Attribute Validation**: Validate subscription IDs and cost centers exist
3. **Budget Limits**: Set appropriate budget limits for managers
4. **Export Controls**: Carefully control who can export sensitive cost data
5. **Audit Logging**: Log all cost data access and modifications

## Next Steps

1. Implement actual Azure Cost Management API integration
2. Create cost models with ABAC mixins
3. Build reporting dashboards
4. Add budget alert notifications
5. Implement cost optimization recommendations

## References

- [RBAC-ABAC Implementation Guide](/docs/RBAC-ABAC-IMPLEMENTATION.md)
- [Identity Provider API Documentation](/identity-provider/docs/API.md)
- [Azure Cost Management API](https://docs.microsoft.com/en-us/rest/api/cost-management/)