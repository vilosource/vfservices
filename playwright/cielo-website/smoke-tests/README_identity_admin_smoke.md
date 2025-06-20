# Identity Admin Users Page Smoke Test

## Overview

This smoke test verifies the basic functionality and health of the Identity Admin Users page at https://website.vfservices.viloforge.com/admin/users/. It focuses on detecting JavaScript errors and ensuring all UI elements are properly displayed.

## Test File

- `test_identity_admin_smoke.py` - Comprehensive smoke test for the Identity Admin Users page

## What is Tested

### 1. JavaScript Error Detection
- Monitors console for JavaScript errors throughout the test
- Catches uncaught exceptions
- Fails the test if any JS errors are detected

### 2. Login Flow
- Logs in as alice user
- Verifies successful authentication

### 3. Page Structure
- Navigation bar presence
- Sidebar menu visibility
- Page title verification ("User Management")

### 4. Filter Controls
- Search input field
- Status filter dropdown
- Role filter dropdown
- Apply and Clear filter buttons

### 5. Table Structure
- Verifies table headers are correct:
  - Username
  - Email
  - Name
  - Status
  - Roles
  - Last Login
  - Actions
- Confirms table has data rows
- Checks each row has 7 cells

### 6. Action Buttons
- View button
- Edit button
- Manage Roles button

### 7. Pagination
- Pagination info display
- User count information

### 8. DataTables Integration
- Verifies DataTables library is initialized
- Checks for responsive wrapper

## Prerequisites

- All services running (identity-provider, website, traefik)
- Alice user exists with:
  - Username: alice
  - Password: alicepassword
  - identity_admin role

## How to Run

### Using pytest (from container):
```bash
docker compose exec website-test python -m pytest playwright/cielo-website/smoke-tests/test_identity_admin_smoke.py -v
```

### Standalone (from host):
```bash
cd playwright/cielo-website/smoke-tests
python test_identity_admin_smoke.py
```

## Expected Output

When successful, the test will print:
```
🔍 Starting Identity Admin Users smoke test...
📍 Navigating to login page...
🔐 Logging in as alice...
📊 Navigating to admin users page...
✅ No JavaScript errors detected
🔍 Checking page elements...
🔍 Checking filter controls...
📋 Verifying table structure...
✅ Table headers are correct
📊 Verifying table data...
✅ Table has X rows
🔍 Checking action buttons...
📄 Checking pagination...
📱 Testing table responsiveness...
📸 Screenshot saved as identity_admin_smoke_test.png

✅ Identity Admin Users smoke test completed successfully!
   - No JavaScript errors
   - All page elements present
   - Table structure correct
   - X users displayed
   - All controls functional
```

## Troubleshooting

### JavaScript Errors
If the test fails with JavaScript errors:
1. Check browser console for specific error messages
2. Verify all static files are loading correctly
3. Check for missing API endpoints
4. Ensure proper CORS configuration

### Login Failures
1. Verify alice user exists in the database
2. Check password is correct
3. Ensure identity-provider service is running

### Table Not Loading
1. Check API endpoints are accessible
2. Verify alice has identity_admin role
3. Check for network errors in browser console

### Missing Elements
1. Verify static files are being served
2. Check for CSS/JS loading errors
3. Ensure proper template rendering

## Screenshot

The test captures a screenshot (`identity_admin_smoke_test.png`) for visual verification. This is automatically cleaned up after the test completes when run standalone.

## CI/CD Integration

This smoke test is ideal for CI/CD pipelines as it:
- Runs quickly (typically < 10 seconds)
- Provides clear pass/fail status
- Detects critical JavaScript errors
- Verifies essential UI functionality
- Requires no manual intervention