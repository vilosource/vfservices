# Demo Troubleshooting Guide

This guide helps troubleshoot common issues with the RBAC-ABAC demo system and the interactive demo pages.

## Issues Found and Fixed

### 1. **Services Not Registering Their Manifests**
**Problem**: The billing and inventory APIs only registered when `DEBUG=False`, but Docker was running with `DEBUG=True`.

**Fix**: Removed the debug check from service registration in `billing-api/billing/apps.py` and `inventory-api/inventory/apps.py`.

### 2. **ALLOWED_HOSTS Configuration**
**Problem**: Services couldn't communicate using internal Docker hostnames.

**Fix**: Added Docker service names to ALLOWED_HOSTS in all service settings.

### 3. **Service Registration Errors**
**Problem**: The `ManifestService.register_manifest()` had parameter mismatches and type errors.

**Fix**: 
- Changed `service_manifest` parameter to `manifest`
- Fixed return type from Response to dict

### 4. **No Roles Assigned to Users**
**Problem**: Demo users had attributes but no roles in the database.

**Fix**: The `setup_demo_users` command now properly creates and assigns roles.

### 5. **JWT Missing User ID**
**Problem**: JWT tokens didn't include the user ID, preventing RBAC attribute loading.

**Fix**: Added `user_id` to JWT payload in identity provider login view.

### 6. **JWT Middleware Issues**
**Problem**: Middleware couldn't load user attributes without the user ID.

**Fix**: Updated `JWTAuthenticationMiddleware` to use `user_id` from JWT payload.

## Current Status

### Alice's Permissions (Working Correctly)
- **Roles**: billing_admin, customer_manager
- **Attributes**: 
  - department: Management
  - customer_ids: [100, 200, 300, 400, 500]
  - invoice_limit: 50000
  - can_export_data: true

### What Alice Can Do
✅ Access billing private data (has billing_admin role)
✅ Manage customers (has customer_manager role)
✅ View all billing information
✅ Process high-value transactions (up to $50,000)

### What Alice Cannot Do
❌ Create invoices (needs invoice_manager role)
❌ View payments directly (needs payment_viewer role)
❌ Access warehouse management (needs inventory roles)

## How to Verify Everything is Working

### Using the Demo Pages (Recommended)

1. **Check Setup Status**:
   - Navigate to `http://website.vfservices.viloforge.com/demo/`
   - The dashboard shows:
     - Services registered count (should be 3)
     - Users created count (should be 4)
     - Roles assigned count (should be > 0)
     - Overall setup status indicator

2. **Verify User Permissions**:
   - Go to RBAC Dashboard (`/demo/rbac/`)
   - Switch between users to see their permissions
   - Compare expected vs. actual permissions

3. **Test API Access**:
   - Use API Explorer (`/demo/api/`)
   - Test different endpoints with different users
   - Green status codes = success, red = failure

### Using Command Line

1. **Check Service Registration**:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py shell
from identity_app.models import Service
Service.objects.all()  # Should show billing_api, inventory_api
```

2. **Check User Roles**:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py shell
from django.contrib.auth.models import User
from identity_app.models import UserRole
user = User.objects.get(username='alice')
UserRole.objects.filter(user=user).values_list('role__name', 'role__service__name')
```

3. **Check Redis Cache**:
```bash
docker exec -it vfservices-redis-1 redis-cli
KEYS user:*:attrs:*
GET user:4:attrs:billing_api  # Alice is user ID 4
```

4. **Test API Access**:
- Login as Alice in the demo
- Go to API Explorer
- Test billing private endpoint - should work
- Test inventory private endpoint - should fail (no inventory roles)

## Common Issues and Solutions

### Issue: "Demo pages not loading"
**Symptoms**: 
- 404 errors on `/demo/` URLs
- "Page not found" errors

**Solutions**:
1. Ensure you're logged in first
2. Check that website service is running
3. Verify URL includes `/demo/` prefix

### Issue: "No demo users found"
**Symptoms**:
- User switcher shows no users
- API Explorer shows no current user
- Permission matrix is empty

**Solution**: Run the setup command:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py setup_demo_users
```

### Issue: "No roles assigned"
**Symptoms**:
- RBAC Dashboard shows empty permissions
- API calls return 403 Forbidden
- Permission matrix has no checkmarks

**Solution**: Run the complete setup command:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py complete_demo_setup
```

### Issue: "Service not registered"
**Solution**: Restart the service to trigger registration:
```bash
docker-compose restart billing-api
docker-compose restart inventory-api
```

### Issue: "Redis cache empty" or "Stale permissions"
**Symptoms**:
- RBAC Dashboard shows outdated permissions
- API access doesn't match assigned roles
- Permission changes not reflected

**Solution**: Use the refresh command:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py refresh_demo_cache
```

This command:
- Refreshes cache for all demo users (alice, bob, charlie, david)
- Updates all services (billing_api, inventory_api, identity_provider)
- Shows success/failure for each update

**Alternative manual method**:
```bash
docker exec -it vfservices-identity-provider-1 python manage.py shell
from identity_app.services import RedisService
from django.contrib.auth.models import User
user = User.objects.get(username='alice')
RedisService.populate_user_attributes(user.id, 'billing_api')
```

### Issue: "JWT token invalid"
**Solution**: Clear browser cookies and login again to get a fresh token with user_id.

## Expected Demo Behavior

### Demo Page Functionality

1. **Demo Dashboard** (`/demo/`):
   - Shows all 4 demo users
   - Displays setup completion status
   - User switcher works instantly
   - Navigation to other demo pages

2. **RBAC Dashboard** (`/demo/rbac/`):
   - Shows current user's roles by service
   - Displays user attributes (department, limits, etc.)
   - Updates when switching users

3. **API Explorer** (`/demo/api/`):
   - Lists all available endpoints
   - Shows authentication requirements
   - Returns appropriate status codes
   - Displays full response data

4. **Permission Matrix** (`/demo/matrix/`):
   - Shows all users and roles
   - Checkmarks for assigned roles
   - Grouped by service
   - Hover for role descriptions

5. **Access Playground** (`/demo/playground/`):
   - Pre-configured scenarios run successfully
   - Step-by-step execution visible
   - Appropriate successes/failures

### API Access Patterns

When testing as Alice:
1. **Billing API /private/**: ✅ Should succeed (billing_admin role)
2. **Billing API /billing-admin/**: ✅ Should succeed (has role)
3. **Billing API /invoice-manager/**: ❌ Should fail (no role)
4. **Inventory API /inventory-manager/**: ✅ Should succeed (has role)
5. **Identity API /profile/**: ✅ Should succeed (authenticated)

When testing as Bob:
1. **Billing API /invoice-manager/**: ✅ Should succeed
2. **Billing API /billing-admin/**: ❌ Should fail
3. **Inventory API /stock-viewer/**: ✅ Should succeed
4. **Inventory API /warehouse-manager/**: ❌ Should fail

The permission checks are working correctly when you see these patterns!

## Quick Fixes

### Complete Reset and Setup
```bash
# Stop all services
docker compose down

# Start fresh
docker compose up -d

# Wait for services to start (30 seconds)
sleep 30

# Run complete setup
docker exec -it vfservices-identity-provider-1 python manage.py complete_demo_setup

# Refresh cache
docker exec -it vfservices-identity-provider-1 python manage.py refresh_demo_cache
```

### Verify Everything
1. Go to `http://website.vfservices.viloforge.com/demo/`
2. Check setup status shows all green
3. Try switching between users
4. Test some API endpoints
5. View the permission matrix

If all these work, the demo is fully operational!