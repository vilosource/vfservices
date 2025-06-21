# Playwright Test Migration Examples

This document shows how to migrate common test patterns to use the authentication utility.

## Basic Login Pattern

### Before:
```python
# Navigate to login page
page.goto("https://identity.vfservices.viloforge.com/login/")
page.fill('input[name="username"]', 'admin')
page.fill('input[name="password"]', 'admin123')
page.click('button[type="submit"]')
page.wait_for_load_state("networkidle")

# ... perform tests ...

# Manual logout
page.goto("https://identity.vfservices.viloforge.com/logout/")
```

### After:
```python
from playwright.common.auth import authenticated_page

with authenticated_page(page, "admin", "admin123") as auth_page:
    # User is already logged in
    # ... perform tests ...
# Automatic logout happens here
```

## Service-Specific Login

### Before:
```python
# Login and navigate to CIELO
page.goto("https://cielo.viloforge.com/accounts/login/")
page.fill('input[name="email"]', 'alice')
page.fill('input[name="password"]', 'password123')
page.click('button[type="submit"]')
page.wait_for_load_state("networkidle")

# Check if user has access
if "cielo.viloforge.com" not in page.url:
    pytest.skip("User doesn't have CIELO access")
```

### After:
```python
from playwright.common.auth import authenticated_page, AuthenticationError

try:
    with authenticated_page(page, "alice", "password123", 
                          service_url="https://cielo.viloforge.com") as auth_page:
        # User is logged in and has access to CIELO
        # ... perform tests ...
except AuthenticationError as e:
    pytest.skip(f"User doesn't have CIELO access: {e}")
```

## Class-Based Tests

### Before:
```python
class TestIdentityAdmin:
    def setup(self, page):
        self.page = page
        self.login()
    
    def login(self):
        self.page.goto("https://identity.vfservices.viloforge.com/login/")
        self.page.fill('input[name="username"]', 'admin')
        self.page.fill('input[name="password"]', 'admin123')
        self.page.click('button[type="submit"]')
        self.page.wait_for_load_state("networkidle")
    
    def test_something(self):
        # ... test code ...
```

### After:
```python
from playwright.common.auth import authenticated_page

class TestIdentityAdmin:
    def test_something(self, page):
        with authenticated_page(page, "admin") as auth_page:
            # ... test code using auth_page instead of self.page ...
```

## JWT Token Extraction

### Before:
```python
# Login
page.goto("https://identity.vfservices.viloforge.com/login/")
# ... login steps ...

# Get JWT token
cookies = page.context.cookies()
jwt_token = None
for cookie in cookies:
    if cookie["name"] == "jwt_token":
        jwt_token = cookie["value"]
        break

# Or from localStorage
jwt_token = page.evaluate("localStorage.getItem('jwt_token')")
```

### After:
```python
with authenticated_page(page, "admin") as auth_page:
    # Get JWT token easily
    jwt_token = auth_page.get_jwt_token()
    
    # Use for API calls
    headers = {"Authorization": f"Bearer {jwt_token}"}
```

## Multiple Sequential Logins

### Before:
```python
# Test as admin
page.goto("https://identity.vfservices.viloforge.com/login/")
page.fill('input[name="username"]', 'admin')
page.fill('input[name="password"]', 'admin123')
page.click('button[type="submit"]')
# ... admin tests ...
page.goto("https://identity.vfservices.viloforge.com/logout/")

# Test as alice
page.goto("https://identity.vfservices.viloforge.com/login/")
page.fill('input[name="username"]', 'alice')
page.fill('input[name="password"]', 'password123')
page.click('button[type="submit"]')
# ... alice tests ...
page.goto("https://identity.vfservices.viloforge.com/logout/")
```

### After:
```python
# Test as admin
with authenticated_page(page, "admin") as auth_page:
    # ... admin tests ...

# Test as alice
with authenticated_page(page, "alice", "password123") as auth_page:
    # ... alice tests ...
```

## Error Handling

### After (with proper error handling):
```python
from playwright.common.auth import authenticated_page, AuthenticationError

try:
    with authenticated_page(page, "testuser", "wrongpassword") as auth_page:
        # This won't execute if login fails
        pass
except AuthenticationError as e:
    print(f"Login failed as expected: {e}")
    # Handle the error appropriately
```

## Migration Checklist

1. **Add imports** at the top of the file:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
   from playwright.common.auth import authenticated_page, AuthenticationError
   ```

2. **Replace login code** with `authenticated_page` context manager

3. **Remove manual logout code** - it's handled automatically

4. **Update variable names** - use `auth_page` instead of `page` inside the context

5. **Add error handling** where appropriate

6. **Test the migration** - run the test to ensure it still works