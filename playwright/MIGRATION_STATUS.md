# Playwright Test Migration Status

## Overview
This document tracks the migration of Playwright tests to use the new authentication utility (`playwright/common/auth.py`).

## ✅ Completed Migrations

### 1. Authentication Utility Created
- **File**: `playwright/common/auth.py`
- **Features**: Context manager, automatic login/logout, JWT token extraction, error handling

### 2. Example Files Migrated
- `playwright/azure-costs/smoke-tests/test_azure_costs_browser.py` - Partial migration
- `playwright/azure-costs/smoke-tests/test_azure_costs_policies.py` - Login method migrated
- `playwright/cielo-website/smoke-tests/test_cielo_index.py` - Full login/logout flow migrated
- `playwright/cielo-website/smoke-tests/test_cielo_auth_flow_refactored.py` - Complete example
- `playwright/identity-admin/smoke-tests/test_alice_access.py` - Fully migrated

### 3. Documentation Created
- `playwright/common/README.md` - Usage guide for the authentication utility
- `playwright/common/example_refactored_test.py` - Working examples
- `playwright/migration_examples.md` - Migration patterns and examples

## 🔄 Migration Needed

### High Priority (Tests with complex login flows)
1. **CIELO Website Smoke Tests** (14 files)
   - Contains login/logout flows that need migration
   - Service-specific authentication patterns

2. **Identity Admin Smoke Tests** (13 files remaining)
   - Admin authentication patterns
   - Role-based access tests

3. **CIELO Website Integration Tests** (3 files)
   - Cross-service authentication tests
   - Multiple user login scenarios

### Medium Priority
4. **Identity Provider Smoke Tests**
   - API-based authentication tests
   - May need custom handling for API tokens

5. **Website Smoke Tests** (3 files)
   - Basic authentication patterns

## 🛠️ How to Complete the Migration

### For each test file:

1. **Add imports** at the top:
```python
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from playwright.common.auth import authenticated_page, AuthenticationError
```

2. **Replace login sequences** with the context manager:
```python
# Instead of manual login steps
with authenticated_page(page, "username", "password") as auth_page:
    # Use auth_page for all operations
    auth_page.goto("https://example.com/protected")
    # ... tests ...
# Automatic logout happens here
```

3. **Update variable references**:
- Replace `page` with `auth_page` inside the context
- Remove manual logout code

4. **Add error handling** where appropriate:
```python
try:
    with authenticated_page(page, "user", "pass", service_url="https://service.com") as auth_page:
        # Tests requiring specific service access
except AuthenticationError as e:
    pytest.skip(f"User lacks access: {e}")
```

## 📋 Migration Checklist

- [ ] Review all test files in `playwright/` directory
- [ ] Migrate login/logout patterns to use `authenticated_page`
- [ ] Test each migrated file to ensure it works
- [ ] Remove backup files after verification
- [ ] Update any CI/CD configurations if needed

## 🚀 Benefits of Migration

1. **Reduced Code Duplication**: No more copy-pasting login code
2. **Consistent Error Handling**: All auth errors handled uniformly
3. **Automatic Cleanup**: Logout always happens, even on test failure
4. **JWT Token Access**: Easy token extraction for API tests
5. **Maintainability**: Auth changes only need updates in one place

## ⚠️ Special Considerations

1. **Custom Login Flows**: Some tests may have unique login requirements that need manual adjustment
2. **API Tests**: Tests that use JWT tokens directly may need the `get_jwt_token()` method
3. **Multiple Users**: Tests with sequential logins can use nested context managers
4. **Service-Specific Auth**: Use the `service_url` parameter for service-specific login flows

## 📝 Notes

- The authentication utility supports both `username` and `email` login fields
- Default password pattern is `{username}123!#QWERT` if not specified
- The utility handles various logout patterns (links, buttons, direct navigation)
- All tests should use `ignore_https_errors=True` for self-signed certificates

## Next Steps

1. Prioritize migration of frequently-used test suites
2. Run migrated tests to verify functionality
3. Update team documentation and training materials
4. Consider adding more features to the auth utility as needed