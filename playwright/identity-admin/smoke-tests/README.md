# Identity Admin Smoke Tests

This directory contains Playwright smoke tests for the Identity Admin Django application.

## Tests

### 1. test_identity_admin_dashboard.py
Tests the basic dashboard functionality and CSS loading for the Identity Admin interface.

**What it tests:**
- Login functionality with admin user
- Navigation to Identity Admin dashboard
- CSS loading verification
- Basic page structure validation

### 2. test_admin_dashboard.py
Tests admin user access to the Identity Admin dashboard.

**What it tests:**
- Admin user authentication
- Dashboard page title verification
- Menu item visibility
- Basic dashboard content

### 3. test_user_list.py
Tests the user list view functionality.

**What it tests:**
- Navigation from dashboard to user list
- User table rendering
- Presence of admin and alice users
- Search and filter controls
- Create User button visibility

### 4. test_user_detail.py
Tests the user detail and edit view functionality.

**What it tests:**
- User detail page rendering
- User information display
- Role assignment display
- Edit user form functionality
- Navigation between detail and edit views

### 5. test_user_roles.py
Tests the role management interface.

**What it tests:**
- Current roles display
- Role assignment form
- Service and role selection
- Quick assignment profiles
- Form interactivity

### 6. test_alice_access.py
Tests user access with proper role assignment.

**What it tests:**
- Alice's access to Identity Admin with identity_admin role
- JWT token refresh after role assignment
- Proper authorization checks

### 7. test_identity_admin_comprehensive.py
Comprehensive test suite that runs all tests systematically.

**What it tests:**
- Authentication and authorization (3 tests)
- Dashboard functionality (9 tests)
- User list view (8 tests)
- User detail view (8 tests)
- User edit functionality (8 tests)
- Role management (7 tests)
- Navigation and UI elements (3 tests)
- Search and filter functionality (4 tests)

Total: 49 automated tests covering all major functionality

## Running the Tests

To run all tests:
```bash
cd /home/jasonvi/GitHub/vfservices
python playwright/identity-admin/smoke-tests/test_identity_admin_dashboard.py
python playwright/identity-admin/smoke-tests/test_admin_dashboard.py
python playwright/identity-admin/smoke-tests/test_user_list.py
```

To run a specific test:
```bash
python playwright/identity-admin/smoke-tests/test_user_list.py
```

## Prerequisites

1. Docker containers must be running:
   ```bash
   docker compose up -d
   ```

2. The admin user must exist with the identity_admin role:
   - Username: admin
   - Password: admin123
   - Role: identity_admin (for website service)

3. Playwright must be installed:
   ```bash
   pip install playwright
   playwright install chromium
   ```

## Test URLs

The tests use the following Traefik endpoints:
- Identity Provider: https://identity.vfservices.viloforge.com
- Website (Identity Admin): https://website.vfservices.viloforge.com/admin/

## Debugging

The tests run with `headless=False` by default to allow visual debugging. To run in headless mode, change:
```python
browser = p.chromium.launch(headless=False)
```
to:
```python
browser = p.chromium.launch(headless=True)
```

## Screenshots

Tests save screenshots to help with debugging:
- `identity_admin_dashboard_styled.png` - Dashboard with CSS verification
- `identity_admin_dashboard_admin.png` - Admin user dashboard access
- `identity_admin_user_list.png` - User list view

## Common Issues

1. **Blank screenshots**: The application uses JavaScript to render content. Screenshots may appear blank due to timing issues, but the tests verify that content is actually present in the DOM.

2. **Authentication errors**: Ensure the admin user has the identity_admin role for the website service.

3. **404 errors**: Verify that the identity_admin app is properly installed in the website Django project and URLs are configured correctly.