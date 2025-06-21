# Identity Provider Admin API Testing Documentation

## Overview

The Identity Provider service provides comprehensive admin APIs for managing users, roles, and permissions. This document covers the testing approach, implementation details, and key fixes that were applied to make the admin API tests functional.

## Admin API Endpoints

The Identity Provider exposes the following admin API endpoints:

### User Management
- `GET /api/admin/users/` - List all users with pagination
- `POST /api/admin/users/` - Create a new user
- `GET /api/admin/users/{id}/` - Get user details
- `PUT /api/admin/users/{id}/` - Update user details
- `DELETE /api/admin/users/{id}/` - Deactivate user (soft delete)
- `POST /api/admin/users/{id}/set-password/` - Set user password
- `GET /api/admin/users/{id}/roles/` - List user's roles
- `POST /api/admin/users/{id}/roles/` - Assign role to user
- `DELETE /api/admin/users/{id}/roles/{role_id}/` - Revoke role from user

### Role Management
- `GET /api/admin/roles/` - List all roles
- `GET /api/admin/services/` - List all services

### Bulk Operations
- `POST /api/admin/bulk/assign-roles/` - Bulk assign roles to users

### Audit
- `GET /api/admin/audit-log/` - View audit log entries

## Authentication

All admin API endpoints require:
1. JWT authentication (via cookie or Bearer token)
2. The user must have the `identity_admin` role

## Implementation Details

### Custom Authentication Class

To bypass CSRF protection for API endpoints while maintaining JWT authentication, a custom authentication class was implemented:

```python
class JWTCookieAuthentication(BaseAuthentication):
    """
    Custom authentication class that uses JWT from cookies
    but doesn't trigger CSRF checks like SessionAuthentication
    """
    def authenticate(self, request):
        # The JWT middleware has already authenticated the user
        # Check the underlying WSGIRequest, not the DRF request wrapper
        if hasattr(request._request, 'user') and request._request.user.is_authenticated:
            return (request._request.user, None)
        return None
```

This class is applied to all admin ViewSets:

```python
class UserViewSet(ModelViewSet):
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsIdentityAdmin]
    # ... rest of the configuration
```

### JWT User Handling

The JWT middleware creates `JWTUser` objects which are not Django User instances. For database operations that require a Django User (like setting `granted_by`), a helper function was added:

```python
def get_django_user(request):
    """Get Django User instance from request"""
    if hasattr(request.user, 'id') and request.user.id:
        try:
            return User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            pass
    return None
```

### Key Model Field Names

The UserRole model uses these field names:
- `granted_by` - The user who granted the role (not `assigned_by`)
- `granted_at` - When the role was granted (not `assigned_at`)
- `expires_at` - Optional expiration date for the role

### Service Methods

The RedisService provides these methods for cache management:
- `populate_user_attributes(user_id, service_name)` - Populate Redis cache
- `invalidate_user_cache(user_id, service_name=None)` - Clear cache entries

## Testing Approach

### Test Structure

Tests are located in `playwright/identity-provider/smoke-tests/`:

```
smoke-tests/
├── conftest.py              # Pytest fixtures and configuration
├── test_setup_verification.py   # Service availability tests
├── test_debug_auth.py          # Authentication debugging
├── test_admin_api_simple.py    # Simple direct HTTP tests
├── test_admin_api_users.py     # User management tests
├── test_admin_api_roles.py     # Role management tests
├── test_admin_api_bulk.py      # Bulk operations tests
└── test_admin_api_integration.py # Integration tests
```

### Working Test Pattern

Direct HTTP requests work reliably:

```python
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://identity.vfservices.viloforge.com"

def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/login/",
        json={"username": "admin", "password": "admin123"},
        verify=False
    )
    return response.json()['token']

def test_list_users():
    """Test listing users"""
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
    
    assert response.status_code == 200
```

### Browser-Based Tests (Currently Failing)

Tests using `page.evaluate()` for API calls are failing due to authentication context issues:

```python
# This pattern currently fails
response = api_client.get('api/admin/users/')
```

These tests need to be rewritten to use direct HTTP requests.

## Common Issues and Solutions

### 1. CSRF Protection
**Issue**: POST/PUT/DELETE requests fail with "CSRF Failed: CSRF cookie not set"
**Solution**: Use Bearer token authentication in headers instead of cookie-based auth, or implement custom authentication class

### 2. Field Name Mismatches
**Issue**: Database errors about unknown fields
**Solution**: Use correct field names:
- `granted_by` not `assigned_by`
- `granted_at` not `assigned_at`

### 3. Method vs Property
**Issue**: `TypeError: 'bool' object is not callable`
**Solution**: `is_active` is a property, not a method - use `obj.is_active` not `obj.is_active()`

### 4. JWT User vs Django User
**Issue**: `ValueError: Cannot assign JWTUser object`
**Solution**: Convert JWT user to Django User instance using the helper function

### 5. Cache Method Names
**Issue**: `AttributeError: 'RedisService' object has no attribute`
**Solution**: Use correct method names:
- `populate_user_attributes()` not `cache_user_attributes()`
- `invalidate_user_cache()` not `delete_user_attributes()`

## Running Tests

### Prerequisites
1. All services running via Docker Compose
2. Admin user exists with `identity_admin` role
3. Domain resolution configured in `/etc/hosts`

### Run Individual Tests
```bash
cd playwright/identity-provider/smoke-tests
python test_admin_api_simple.py
```

### Run All Tests
```bash
make test-identity-admin
```

### Debug Failed Tests
```bash
# Check service logs
docker compose logs identity-provider

# Run with visible output
python -m pytest test_admin_api_simple.py -v -s

# Run specific test
python -m pytest test_admin_api_simple.py::test_create_user -v
```

## Future Improvements

1. **Update Browser-Based Tests**: Rewrite tests using `page.evaluate()` to use direct HTTP requests
2. **Add Performance Tests**: Test bulk operations with large datasets
3. **Cache Validation**: Add tests to verify Redis cache invalidation
4. **Audit Log Tests**: Comprehensive testing of audit log functionality
5. **Error Scenarios**: More edge case and error handling tests
6. **Integration Tests**: Cross-service permission checks

## Related Documentation

- [Identity Provider README](../README.md)
- [RBAC-ABAC System Documentation](../../docs/RBAC-ABAC.md)
- [API Documentation](./api.md)
- [Logging Configuration](./Logging.md)