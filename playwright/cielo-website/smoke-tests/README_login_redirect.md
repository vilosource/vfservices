# Login Redirect Tests

## Overview
This test suite verifies the login redirect functionality for the Cielo website, ensuring users are properly redirected after authentication.

## Test Cases

### 1. `test_login_redirect_to_homepage`
- Tests that logging in without a `next` parameter redirects to the homepage (`/`)
- Verifies authentication by checking for the logout link

### 2. `test_login_redirect_with_next_parameter`
- Tests that accessing a protected page redirects to login with the `next` parameter preserved
- Verifies that after login, the user is redirected to the originally requested page
- Example: Accessing `/management/` → Redirected to `/accounts/login/?next=/management/` → After login → Redirected to `/management/`

### 3. `test_authenticated_user_accessing_login_redirects_home`
- Tests that an already authenticated user trying to access the login page is redirected to the homepage
- Prevents authenticated users from seeing the login form unnecessarily

## Running the Tests

```bash
# Run all login redirect tests
pytest playwright/cielo-website/smoke-tests/test_login_redirect.py -v

# Run a specific test
pytest playwright/cielo-website/smoke-tests/test_login_redirect.py::test_login_redirect_with_next_parameter -v

# Run with headed browser for debugging
pytest playwright/cielo-website/smoke-tests/test_login_redirect.py -v --headed
```

## Test User
- Username: `alice`
- Password: `password123`

## Requirements
- Access to https://cielo.viloforge.com
- Valid test user credentials
- Playwright and pytest installed