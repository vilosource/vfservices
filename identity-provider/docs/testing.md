# Identity Provider Testing Documentation

## Overview

This document describes the testing approach for the Identity Provider service, including how to run tests, what is tested, and the testing philosophy.

## Running Tests

### Running All Tests

To run all tests for the Identity Provider:

```bash
python manage.py test identity_app --settings=main.test_settings_jwt -v 2
```

### Running Specific Test Suites

#### Basic API Endpoint Tests
```bash
python manage.py test identity_app.tests.test_api_endpoints --settings=main.test_settings_jwt
```

#### Admin API Tests
```bash
python manage.py test identity_app.tests.test_admin_api_complete --settings=main.test_settings_jwt
```

### Running Individual Test Cases

You can run specific test classes or methods:

```bash
# Run a specific test class
python manage.py test identity_app.tests.test_api_endpoints.LoginAPITestCase --settings=main.test_settings_jwt

# Run a specific test method
python manage.py test identity_app.tests.test_api_endpoints.LoginAPITestCase.test_login_success --settings=main.test_settings_jwt
```

### Test Settings

The tests use a special settings file `main.test_settings_jwt.py` that:
- Uses an in-memory SQLite database for faster tests
- Configures JWT authentication middleware
- Sets a test JWT secret key
- Disables migrations for faster test runs

## What is Tested

### Basic API Endpoints (`test_api_endpoints.py`)

1. **Authentication Endpoints**
   - `/api/login/` - API login with username/password
   - Login success and failure scenarios
   - Invalid credentials handling
   - Missing field validation

2. **Profile Endpoint**
   - `/api/profile/` - Get authenticated user profile
   - Requires valid JWT authentication
   - Returns user information and roles

3. **Service Registration**
   - `/api/services/register/` - Register new services
   - Service manifest validation
   - Role creation from manifest
   - Duplicate service handling

4. **Cache Management**
   - `/api/refresh-user-cache/` - Force cache refresh
   - Redis cache invalidation
   - Error handling when Redis is unavailable

### Admin API Endpoints (`test_admin_api_complete.py`)

1. **User Management**
   - List users with pagination and filtering
   - Create new users with initial roles
   - Update user information
   - Deactivate users (soft delete)
   - Set/reset passwords
   - Search users by name/email

2. **Role Management**
   - List all roles
   - Filter roles by service or global status
   - Get role details

3. **User-Role Assignment**
   - List user's current roles
   - Assign roles to users
   - Set role expiration dates
   - Revoke roles from users
   - Prevent duplicate role assignments

4. **Service Management**
   - List active services
   - Get service details with role/user counts

5. **Bulk Operations**
   - Bulk assign roles to multiple users
   - Handle partial failures gracefully
   - Transaction safety

6. **Permissions**
   - All admin endpoints require `identity_admin` role
   - JWT authentication required
   - Proper 403 responses for unauthorized access

## Testing Philosophy

### 1. Comprehensive Coverage

- Test both success and failure scenarios
- Cover edge cases (e.g., expired roles, duplicate assignments)
- Test permission boundaries

### 2. Isolation

- Each test is independent and can run in any order
- Tests use transaction rollback for database isolation
- Mock external dependencies (Redis, JWT authentication)

### 3. Realistic Test Data

- Use meaningful test data that reflects production usage
- Follow password policies (e.g., `username123!#QWERT`)
- Create proper relationships between entities

### 4. JWT Authentication Testing

- Tests use JWT authentication mocking to simulate authenticated requests
- The `JWTCookieAuthentication` class is mocked in tests to return test users
- Both authenticated and unauthenticated scenarios are tested

### 5. Error Handling

- Test invalid inputs and error responses
- Verify appropriate HTTP status codes
- Check error message content and format

## Adding New Tests

### 1. Test Structure

```python
class YourTestCase(TestCase):
    def setUp(self):
        """Set up test data - runs before each test method"""
        # Create test users, services, roles
        
    def tearDown(self):
        """Clean up - runs after each test method"""
        # Stop any patches or clean up resources
        
    def test_your_feature(self):
        """Test description"""
        # Arrange - set up specific test conditions
        # Act - perform the action being tested
        # Assert - verify the results
```

### 2. JWT Authentication in Tests

For endpoints requiring authentication:

```python
from unittest.mock import patch

class AdminAPITestCase(TestCase):
    def setUp(self):
        # Set up JWT authentication mocking
        self.jwt_auth_patcher = patch('identity_app.admin_views.JWTCookieAuthentication.authenticate')
        self.mock_jwt_auth = self.jwt_auth_patcher.start()
        
        # Create admin user
        self.admin_user = User.objects.create_user(...)
        
        # Mock authentication to return admin user
        self.mock_jwt_auth.return_value = (self.admin_user, None)
```

### 3. Testing Best Practices

1. **Use Descriptive Test Names**: Test method names should clearly describe what is being tested
2. **One Assertion Per Test**: Keep tests focused on a single behavior
3. **Use Fixtures Wisely**: Create reusable test data in setUp methods
4. **Mock External Dependencies**: Mock Redis, external APIs, etc.
5. **Test Edge Cases**: Empty lists, None values, expired data, etc.
6. **Verify Side Effects**: Check cache invalidation, audit logs, etc.

### 4. Common Test Patterns

#### Testing API Endpoints
```python
def test_endpoint_success(self):
    url = reverse('endpoint-name')
    data = {'field': 'value'}
    response = self.client.post(url, data, format='json')
    
    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.json()['field'], 'value')
```

#### Testing Permissions
```python
def test_requires_permission(self):
    # Test without permission
    self.authenticate_as_regular_user()
    response = self.client.get(url)
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # Test with permission
    self.authenticate_as_admin()
    response = self.client.get(url)
    self.assertEqual(response.status_code, status.HTTP_200_OK)
```

#### Testing Cache Invalidation
```python
@patch('identity_app.services.RedisService.invalidate_user_cache')
def test_cache_invalidation(self, mock_invalidate):
    # Perform action that should invalidate cache
    response = self.client.post(url, data)
    
    # Verify cache was invalidated
    mock_invalidate.assert_called_with(user_id)
```

## Continuous Integration

Tests should be run in CI/CD pipelines with:
- Coverage reporting (aim for >80% coverage)
- Parallel test execution for speed
- Test result reporting
- Failure notifications

## Performance Testing

For API endpoints, consider:
- Response time assertions
- Database query count limits
- Pagination testing with large datasets
- Concurrent request handling