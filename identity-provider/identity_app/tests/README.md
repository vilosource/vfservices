# Identity Provider API Tests

This directory contains comprehensive unit tests for the Identity Provider API endpoints.

## Test Files

### test_api_endpoints.py
Tests for basic API endpoints including:
- Login API (`/api/login/`)
- Web-based login/logout (`/login/`, `/logout/`)
- API information endpoints (`/api/`, `/api/status/`)
- User profile endpoint (`/api/profile/`)
- Service registration (`/api/services/register/`)
- Cache refresh (`/api/refresh-user-cache/`)

### test_admin_api_complete.py
Comprehensive tests for admin API endpoints including:
- User management (CRUD operations)
- Role assignment and revocation
- Service and role listing
- Bulk operations
- Permissions testing

### test_admin_api.py
Original admin API tests (preserved for compatibility)

### test_models.py
Tests for Django models

### test_services.py
Tests for service layer functionality

## Running Tests

### Run all tests
```bash
cd /home/jasonvi/GitHub/vfservices/identity-provider
python manage.py test identity_app.tests
```

### Run specific test file
```bash
python manage.py test identity_app.tests.test_api_endpoints
python manage.py test identity_app.tests.test_admin_api_complete
```

### Run specific test class
```bash
python manage.py test identity_app.tests.test_api_endpoints.LoginAPITestCase
python manage.py test identity_app.tests.test_admin_api_complete.UserViewSetTestCase
```

### Run specific test method
```bash
python manage.py test identity_app.tests.test_api_endpoints.LoginAPITestCase.test_login_success
```

### Run tests with coverage
```bash
coverage run --source='.' manage.py test identity_app.tests
coverage report
coverage html  # Generate HTML report
```

### Run tests in verbose mode
```bash
python manage.py test identity_app.tests --verbosity=2
```

## Test Database

Tests use a separate test database that is created and destroyed for each test run. The test database name is typically `test_<original_db_name>`.

## Test Users

All test users follow the password pattern: `<USERNAME>123!#QWERT`

Common test users:
- `admin` / `admin123!#QWERT` - Admin user with identity_admin role
- `testuser` / `testuser123!#QWERT` - Regular test user
- `adminuser` / `adminuser123!#QWERT` - Alternative admin user

## Mocking

Some tests use mocking for:
- JWT token generation
- Redis cache operations
- External service calls

## Test Coverage

The tests aim to cover:
- All API endpoints
- Success and error cases
- Authentication and authorization
- Input validation
- Edge cases and error handling

## Adding New Tests

When adding new API endpoints:
1. Add corresponding test cases in the appropriate test file
2. Test both success and error scenarios
3. Test authentication/authorization requirements
4. Test input validation
5. Mock external dependencies as needed

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're running tests from the project root
2. **Database errors**: Check database configuration in test_settings.py
3. **Authentication failures**: Verify JWT middleware configuration
4. **Missing fixtures**: Some tests may require initial data setup

### Debug Mode

To run tests with debugging:
```bash
python manage.py test identity_app.tests --debug-mode
```

Or use pdb:
```python
import pdb; pdb.set_trace()
```

## CI/CD Integration

These tests should be run as part of the CI/CD pipeline to ensure code quality and prevent regressions.