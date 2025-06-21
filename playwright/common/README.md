# Playwright Common Utilities

This directory contains shared utilities for Playwright tests across all services.

## Authentication Utility

The `auth.py` module provides reusable authentication functionality to avoid code duplication in tests.

### Features

- **Automatic login/logout**: Handles the complete authentication flow
- **Context manager support**: Ensures proper cleanup even if tests fail
- **Multiple authentication endpoints**: Supports different identity providers
- **JWT token extraction**: Automatically extracts and provides JWT tokens
- **Error handling**: Provides clear error messages for authentication failures
- **Service-specific navigation**: Can navigate to specific services after login

### Usage

#### Method 1: Context Manager (Recommended)

```python
from playwright.sync_api import sync_playwright
from playwright.common.auth import authenticated_page

def test_admin_functionality():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Use context manager for automatic login/logout
        with authenticated_page(page, "admin", "admin123!#QWERT") as auth_page:
            # User is already logged in here
            auth_page.goto("https://website.vfservices.viloforge.com/admin/")
            
            # Perform your tests
            assert "Identity Administration" in auth_page.title()
            
            # Get JWT token if needed
            token = auth_page.get_jwt_token()
            print(f"JWT Token: {token}")
            
        # User is automatically logged out here
        browser.close()
```

#### Method 2: Manual Login/Logout

```python
from playwright.common.auth import login_user, logout_user

def test_manual_auth():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Manual login
            auth_page = login_user(page, "alice", "alice123!#QWERT")
            
            # Perform tests
            auth_page.goto("https://cielo.viloforge.com/")
            
        finally:
            # Manual logout
            logout_user(auth_page)
            browser.close()
```

#### Method 3: Service-Specific Login

```python
# Login and navigate to a specific service
with authenticated_page(page, "alice", service_url="https://cielo.viloforge.com") as auth_page:
    # Already logged in and navigated to CIELO
    assert "CIELO" in auth_page.title()
```

### Configuration

The authentication utility uses the following defaults:

- **Default password pattern**: `{username}123!#QWERT`
- **Default identity provider**: `https://identity.vfservices.viloforge.com`
- **Supported login fields**: `username` or `email`
- **JWT cookie names**: `jwt`, `jwt_token`, `access_token`

### Error Handling

The utility raises `AuthenticationError` for:
- Invalid credentials
- Missing form fields
- Login timeouts
- Access denied to requested service

Example:
```python
from playwright.common.auth import authenticated_page, AuthenticationError

try:
    with authenticated_page(page, "invalid_user") as auth_page:
        # This will fail
        pass
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### Migration Guide

To migrate existing tests to use the authentication utility:

1. Remove manual login code
2. Import the utility
3. Wrap test code in the context manager

Before:
```python
# Manual login
page.goto("https://identity.vfservices.viloforge.com/login/")
page.fill('input[name="username"]', 'admin')
page.fill('input[name="password"]', 'admin123!#QWERT')
page.click('button[type="submit"]')
page.wait_for_load_state("networkidle")

# ... test code ...

# Manual logout
page.goto("https://identity.vfservices.viloforge.com/logout/")
```

After:
```python
from playwright.common.auth import authenticated_page

with authenticated_page(page, "admin") as auth_page:
    # ... test code ...
```