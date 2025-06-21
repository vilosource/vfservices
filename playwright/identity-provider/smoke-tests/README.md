# Identity Provider Admin API Playwright Tests

This directory contains Playwright tests for the Identity Provider Admin API endpoints.

## Test Files

### JavaScript/Playwright Tests
- `test_api_endpoints.spec.js` - Comprehensive smoke tests for API logout and attributes endpoints (NEW)

### Python Tests
- `test_admin_api_simple.py` - Basic smoke tests using direct HTTP requests
- `test_debug_auth.py` - Authentication debugging tests
- `test_setup_verification.py` - Service setup verification

## Test Status

### ✅ Working Tests

- `test_api_endpoints.spec.js` - API logout and attributes endpoints tests
- `test_admin_api_simple.py` - Basic smoke tests using direct HTTP requests
- `test_debug_auth.py` - Authentication debugging tests
- `test_setup_verification.py` - Service setup verification

### ⚠️ Tests Requiring Updates

The following tests use browser-based API calls via `page.evaluate()` which are currently failing due to authentication issues:

- `test_admin_api_users.py` - User management API tests
- `test_admin_api_roles.py` - Role management API tests
- `test_admin_api_bulk.py` - Bulk operations tests
- `test_admin_api_integration.py` - Integration tests

## Running Tests

### JavaScript/Playwright Tests:
```bash
# Run the new API endpoint tests
cd playwright/identity-provider/smoke-tests
npx playwright test test_api_endpoints.spec.js

# Run with UI mode for debugging
npx playwright test test_api_endpoints.spec.js --ui

# Run with specific environment variables
IDENTITY_PROVIDER_URL=https://identity.vfservices.viloforge.com \
ADMIN_USERNAME=admin \
ADMIN_PASSWORD=admin123!#QWERT \
npx playwright test test_api_endpoints.spec.js
```

### Python Tests:
```bash
cd playwright/identity-provider/smoke-tests
python test_admin_api_simple.py
python test_debug_auth.py
```

### All tests via pytest:
```bash
cd playwright/identity-provider/smoke-tests
python -m pytest -v
```

### Via Makefile:
```bash
make test-identity-admin
```

## Test Implementation Notes

### Authentication
The Identity Provider admin API uses JWT authentication. The custom `JWTCookieAuthentication` class was added to bypass CSRF checks for API endpoints while still maintaining JWT authentication.

### Key Changes Made:
1. Added `JWTCookieAuthentication` class to `identity_app/admin_views.py`
2. Updated all admin ViewSets to use `authentication_classes = [JWTCookieAuthentication]`
3. Fixed field name mismatches (`assigned_by` -> `granted_by`, `assigned_at` -> `granted_at`)
4. Fixed method calls (`delete_user_attributes` -> `invalidate_user_cache`)
5. Added `get_django_user()` helper to convert JWT user to Django user instance
6. Fixed `is_active()` method call to property access in serializers

### Test Patterns

#### Direct HTTP Requests (Working)
```python
import requests

token = get_admin_token()
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
}

response = requests.get(
    f"{BASE_URL}/api/admin/users/",
    headers=headers,
    verify=False
)
```

#### Browser-based API Calls (Currently Failing)
```python
# This pattern is failing due to authentication issues
response = api_client.get('api/admin/users/')
```

## Test Coverage

### API Endpoint Tests (`test_api_endpoints.spec.js`)
- **API Logout Endpoint**
  - Successful logout with JWT bearer token
  - Error handling for missing authentication token
  - Error handling for invalid authentication token
- **User Attributes API**
  - List user attributes (GET /api/admin/users/{id}/attributes/)
  - Create new user attribute (POST /api/admin/users/{id}/set_attribute/)
  - Update existing user attribute
  - Create service-specific attributes
  - Delete user attributes (DELETE /api/admin/users/{id}/attributes/{name}/)
  - Validation of attribute names (lowercase, alphanumeric, underscores only)
- **Service Attributes API**
  - List service attributes (GET /api/admin/attributes/)
  - Create service attribute definitions (POST /api/admin/attributes/)
  - Update service attribute definitions (PATCH /api/admin/attributes/{id}/)
  - Delete service attribute definitions (DELETE /api/admin/attributes/{id}/)
  - Attribute type validation (string, integer, boolean, list types)
  - Filter attributes by service
- **Permission Tests**
  - Reject unauthenticated requests
  - Ensure admin role requirement

### User Management Tests (`test_admin_api_users.py`)
- Authentication and authorization requirements
- Listing users with pagination
- Searching and filtering users
- Creating users with and without initial roles
- Updating user details
- Deactivating users (soft delete)
- Setting user passwords

### Role Management Tests (`test_admin_api_roles.py`)
- Listing user roles
- Assigning roles to users
- Assigning roles with expiration dates
- Preventing duplicate role assignments
- Revoking roles from users
- Listing all services and roles
- Filtering roles by service and global status

### Bulk Operations Tests (`test_admin_api_bulk.py`)
- Bulk role assignments
- Bulk assignments with expiration dates
- Handling partial failures in bulk operations
- Validation error handling
- Audit log access

### Integration Tests (`test_admin_api_integration.py`)
- Complete user lifecycle workflows
- Search and filter combinations
- Concurrent role operations
- Cache invalidation verification
- Error handling and API recovery

## Prerequisites

1. All services must be running via Docker Compose
2. The Identity Provider must be accessible at `https://identity.vfservices.viloforge.com`
3. An admin user must exist with the `identity_admin` role
4. The domain `*.viloforge.com` must resolve to localhost (check /etc/hosts)

## Debugging Failed Tests

If tests fail:

1. Check domain resolution:
   ```bash
   # Verify domains resolve to localhost
   ping -c 1 identity.vfservices.viloforge.com
   
   # If not, add to /etc/hosts:
   # 127.0.0.1 identity.vfservices.viloforge.com
   ```

2. Run setup verification:
   ```bash
   cd playwright/identity-provider/smoke-tests
   python test_setup_verification.py
   ```

3. Check service logs:
   ```bash
   docker compose logs identity-provider
   ```

4. Run simple tests:
   ```bash
   python test_admin_api_simple.py
   ```

## Future Improvements

1. Update failing tests to use direct HTTP requests instead of browser-based API calls
2. Add more comprehensive test coverage for edge cases
3. Implement performance tests for bulk operations
4. Add tests for Redis cache invalidation
5. Create tests for audit logging functionality