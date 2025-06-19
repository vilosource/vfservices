# RBAC-ABAC Demo Quick Reference

## Demo Pages URLs

| Page | URL | Purpose |
|------|-----|---------|
| Demo Dashboard | `/demo/` | Main hub, setup status, user switching |
| RBAC Dashboard | `/demo/rbac/` | View user permissions and attributes |
| API Explorer | `/demo/api/` | Test API endpoints interactively |
| Permission Matrix | `/demo/matrix/` | Visual role assignment grid |
| Access Playground | `/demo/playground/` | Run pre-configured scenarios |

## Demo Users

| User | Password | Role | Key Access |
|------|----------|------|------------|
| alice | alice123 | Senior Manager | Billing admin, Inventory manager |
| bob | bob123 | Billing Specialist | Invoices, Payments, View inventory |
| charlie | charlie123 | Cloud Manager | Warehouse 1 only, No billing |
| david | david123 | Support Rep | Read-only everything |

## Management Commands

```bash
# Complete demo setup (do this first!)
docker exec -it vfservices-identity-provider-1 python manage.py complete_demo_setup

# Refresh Redis cache (after changes)
docker exec -it vfservices-identity-provider-1 python manage.py refresh_demo_cache

# Setup demo users only
docker exec -it vfservices-identity-provider-1 python manage.py setup_demo_users
```

## Quick Start

1. **Start Services**:
   ```bash
   docker compose up -d
   ```

2. **Run Setup** (first time only):
   ```bash
   docker exec -it vfservices-identity-provider-1 python manage.py complete_demo_setup
   ```

3. **Access Demo**:
   - Go to `http://website.vfservices.viloforge.com/`
   - Login with any demo user (e.g., alice/alice123)
   - Navigate to `/demo/`

4. **Test Features**:
   - Switch users in Demo Dashboard
   - Test API endpoints in API Explorer
   - View permissions in RBAC Dashboard
   - Run scenarios in Access Playground

## Common Tasks

### Switch Demo User
1. Go to Demo Dashboard (`/demo/`)
2. Click on any user in the "Demo Users" section
3. User switches instantly without logout

### Test API Access
1. Go to API Explorer (`/demo/api/`)
2. Select a service (Billing, Inventory, Identity)
3. Click "Test" next to any endpoint
4. View response and status code

### Check User Permissions
1. Go to RBAC Dashboard (`/demo/rbac/`)
2. Current user's permissions shown
3. Compare expected vs. actual roles
4. View user attributes

### Run Access Scenarios
1. Go to Access Playground (`/demo/playground/`)
2. Select a scenario
3. Click "Run Scenario"
4. Watch step-by-step execution

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No demo users" | Run `complete_demo_setup` command |
| "Services not registered" | Restart services, run setup again |
| "Stale permissions" | Run `refresh_demo_cache` command |
| "API calls failing" | Check user has required role |
| "Demo pages 404" | Ensure logged in first |

## Key API Endpoints

### Billing API
- `/private/` - Requires authentication
- `/billing-admin/` - Requires billing_admin role
- `/invoice-manager/` - Requires invoice_manager role
- `/payment-processor/` - Requires payment_processor role

### Inventory API
- `/private/` - Requires authentication
- `/inventory-manager/` - Requires inventory_manager role
- `/warehouse-manager/` - Requires warehouse_manager role
- `/stock-viewer/` - Requires stock_viewer role

### Identity Provider
- `/api/login/` - Get JWT token
- `/api/profile/` - View user profile
- `/api/status/` - Check auth status

## Expected Behaviors

### Alice (Senior Manager)
- ✅ Billing admin endpoints
- ✅ Inventory manager endpoints
- ✅ Customer management
- ❌ Invoice creation (needs invoice_manager)

### Bob (Billing Specialist)
- ✅ Invoice management
- ✅ Payment processing
- ✅ View inventory
- ❌ Billing admin endpoints

### Charlie (Cloud Manager)
- ✅ Warehouse management
- ✅ Stock adjustments
- ❌ Any billing endpoints
- ❌ Other warehouses

### David (Support Rep)
- ✅ View all data
- ❌ Any modifications
- ❌ Admin endpoints
- ❌ Management functions