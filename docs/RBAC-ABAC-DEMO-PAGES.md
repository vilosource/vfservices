# RBAC-ABAC Demo Pages Guide

This document provides a comprehensive guide to the interactive demo pages available in the VF Services website for testing and exploring the RBAC-ABAC implementation.

## Overview

The demo pages provide a visual and interactive way to:
- Test different user permissions and access patterns
- Explore API endpoints with real-time feedback
- Visualize the permission matrix across services
- Execute pre-configured access scenarios
- Monitor the RBAC-ABAC system in action

## Accessing the Demo Pages

1. Start the VF Services stack:
   ```bash
   docker compose up --build
   # or for local development:
   make up
   ```

2. Navigate to the website service:
   ```
   http://website.vfservices.viloforge.com/
   ```

3. Login with any demo user (e.g., alice/alice123)

4. Access the demo section:
   ```
   http://website.vfservices.viloforge.com/demo/
   ```

## Demo Page Features

### 1. Demo Dashboard (`/demo/`)

The main hub for all demo features, providing:

**Setup Status Panel**
- Services registered count
- Demo users created count
- Roles assigned count
- Overall setup completion status

**Demo User Switcher**
- Quick switch between demo users without logging out
- Displays current user info and expected permissions
- Shows user's department and description

**Navigation Menu**
- Links to all other demo pages
- Current user indicator
- Quick access to documentation

### 2. RBAC Dashboard (`/demo/rbac/`)

Comprehensive view of user permissions and attributes:

**User Permission Display**
- Current user's roles by service
- Expected vs. actual permissions comparison
- User attributes (department, limits, access lists)
- Real-time Redis cache data

**Service-Level Breakdown**
- Billing API roles and permissions
- Inventory API roles and permissions
- Identity Provider roles
- Color-coded permission indicators

**Permission Verification**
- Green checkmarks for assigned roles
- Red X marks for missing permissions
- Warning indicators for mismatches

### 3. API Explorer (`/demo/api/`)

Interactive API testing interface:

**Endpoint Categories**
- Identity Provider endpoints
- Billing API endpoints
- Inventory API endpoints
- Health check and status endpoints

**For Each Endpoint**
- HTTP method indicator (GET, POST, etc.)
- Authentication requirement status
- Required role information
- One-click testing with current user

**Test Results Panel**
- HTTP status code
- Response headers
- Response body (formatted JSON)
- Success/failure indicators
- Timing information

**Features**
- Auto-includes JWT token for authenticated requests
- Real-time request/response display
- Error message formatting
- Copy response data functionality

### 4. Permission Matrix (`/demo/matrix/`)

Visual grid showing role assignments:

**Matrix Layout**
- Rows: Demo users (Alice, Bob, Charlie, David)
- Columns: All available roles grouped by service
- Cells: Checkmarks for assigned roles

**Interactive Features**
- Hover for role descriptions
- Click to see role details
- Service grouping with headers
- Total role count display

**Visual Indicators**
- Green background for assigned roles
- Gray for unassigned roles
- Service color coding
- User highlighting on hover

### 5. Access Playground (`/demo/playground/`)

Pre-configured scenarios for testing:

**Available Scenarios**

1. **SuperAdmin Full Access**
   - User: Alice
   - Tests: Full access across all services
   - Expected: All requests succeed

2. **Billing Specialist Access**
   - User: Bob
   - Tests: Billing operations, read-only inventory
   - Expected: Mixed success based on roles

3. **Warehouse Manager Access**
   - User: Charlie
   - Tests: Inventory management, no billing access
   - Expected: Inventory success, billing failures

4. **Read-Only Access Pattern**
   - User: David
   - Tests: View operations only
   - Expected: All write operations fail

**Scenario Execution**
- Step-by-step test execution
- Real-time result display
- Success/failure tracking
- Detailed error messages

## Demo User Quick Reference

| User | Password | Primary Role | Key Permissions |
|------|----------|--------------|-----------------|
| alice | alice123 | Senior Manager | Billing admin, Inventory manager, High limits |
| bob | bob123 | Billing Specialist | Invoice/payment management, View inventory |
| charlie | charlie123 | Cloud Infrastructure Manager | Warehouse management, No billing access |
| david | david123 | Customer Service Rep | Read-only access across services |

## Common Demo Workflows

### Testing Role-Based Access

1. Go to API Explorer (`/demo/api/`)
2. Switch to Alice (full access)
3. Test `/billing-admin/` endpoint - Should succeed
4. Switch to Bob
5. Test same endpoint - Should fail (not billing admin)
6. Test `/invoice-manager/` endpoint - Should succeed

### Verifying Attribute-Based Filtering

1. Go to RBAC Dashboard (`/demo/rbac/`)
2. Check Alice's customer_ids: [100, 200, 300, 400, 500]
3. Check Bob's customer_ids: [100, 200, 300]
4. Note the difference in accessible customers

### Exploring Permission Inheritance

1. Go to Permission Matrix (`/demo/matrix/`)
2. Observe Alice's roles across services
3. Note how `billing_admin` provides more access than individual roles
4. Compare with David's limited viewer roles

### Running Access Scenarios

1. Go to Access Playground (`/demo/playground/`)
2. Select "Billing Specialist Access" scenario
3. Click "Run Scenario"
4. Observe the step-by-step execution
5. Review which operations succeeded/failed

## Troubleshooting

### "No demo users found"
Run the setup command:
```bash
python manage.py setup_demo_users
```

### "Services not registered"
Ensure all services are running and have registered their manifests:
```bash
python manage.py complete_demo_setup
```

### "Permission data not loading"
Refresh the Redis cache:
```bash
python manage.py refresh_demo_cache
```

### "API calls failing"
1. Check that all services are running
2. Verify Redis is accessible
3. Ensure user is logged in
4. Check browser console for errors

## Technical Implementation

### Frontend Stack
- Django templates with Bootstrap 5
- Vanilla JavaScript for interactivity
- Fetch API for AJAX requests
- Session-based demo user switching

### Backend Integration
- Django views serving demo pages
- Direct Redis queries for permission data
- Service-to-service API calls
- JWT token management

### Key Files
- Views: `website/demo/views.py`
- Templates: `website/templates/demo/`
- URLs: `website/demo/urls.py`
- Static assets: `website/static/demo/`

## Extending the Demo

### Adding New Scenarios

1. Edit `website/demo/views.py`
2. Add scenario to the `scenarios` list in `playground()` view
3. Define steps and expected outcomes
4. Update the playground template if needed

### Adding New Demo Users

1. Update `DEMO_USERS` in `website/demo/views.py`
2. Run `setup_demo_users` command
3. Assign appropriate roles and attributes
4. Test access patterns

### Customizing API Endpoints

1. Update `API_ENDPOINTS` in `website/demo/views.py`
2. Add new endpoints with descriptions
3. Specify authentication requirements
4. Test with different users

## Best Practices

1. **Always refresh cache** after making permission changes
2. **Use correct demo user** for each test scenario
3. **Check setup status** before running tests
4. **Monitor browser console** for detailed error messages
5. **Test in incognito mode** to avoid session conflicts

## Related Documentation

- [RBAC-ABAC Implementation](./RBAC-ABAC-IMPLEMENTATION.md) - Core system documentation
- [Demo Users Guide](./RBAC-ABAC-DEMO-USERS.md) - Detailed user profiles
- [Testing Guide](./RBAC-ABAC-TESTING-GUIDE.md) - Automated testing procedures
- [Troubleshooting](./DEMO-TROUBLESHOOTING.md) - Common issues and solutions