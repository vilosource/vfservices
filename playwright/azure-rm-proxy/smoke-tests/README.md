# Azure RM Proxy Smoke Tests

This directory contains Playwright-based smoke tests for the Azure RM Proxy API service.

## Test Coverage

### Authentication Tests (`test_authentication.py`)
- JWT token validation
- Bearer token authentication  
- Cookie-based authentication
- Invalid token rejection
- Unauthenticated access denial

### Authorization Tests
- Role-based access control (RBAC)
- Permission requirements for endpoints
- Azure read/write/admin role validation

### Rate Limiting Tests
- Anonymous user rate limits (60 req/min)
- Authenticated user rate limits (120 req/min)
- Rate limit headers validation

### API Endpoint Tests (`test_api_endpoints.py`)
- Subscriptions API
- Resource Groups API
- Virtual Machines API
- Reports API (VM report, hostnames)
- Networking API (virtual networks, routes)
- Error handling (404, 405, invalid params)

## Prerequisites

1. Install test dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure the following services are running:
- Azure RM Proxy at https://arm-proxy.maltacentral.com
- Identity Provider at https://identity.vfservices.viloforge.com

3. Create test users in the identity provider:
- Regular user: `testuser@viloforge.com` with password `testuser123!#QWERT`
- Admin user: `admin@viloforge.com` with password `admin123!#QWERT`

4. Assign appropriate roles to test users:
- Regular user should have `azure:read` role
- Admin user should have `azure:admin` role

## Running Tests

Run all tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest test_authentication.py -v
```

Run with detailed output:
```bash
pytest -v -s
```

Run specific test class or method:
```bash
pytest test_authentication.py::TestAuthentication::test_valid_token_accepted -v
```

## Test Configuration

Tests are configured in `conftest.py` with the following settings:
- ARM Proxy URL: `https://arm-proxy.maltacentral.com`
- Identity Provider URL: `https://identity.vfservices.viloforge.com`
- Browser: Chromium in headless mode
- HTTPS errors are ignored for self-signed certificates

## Debugging Tips

1. **Authentication Issues**: 
   - Check if test users exist in identity provider
   - Verify users have correct roles assigned
   - Check if `REQUIRE_AUTH` is set to `true` in docker-compose.yml

2. **SSL/TLS Issues**:
   - Tests ignore HTTPS errors by default
   - For production, remove `verify=False` from httpx calls

3. **Rate Limiting**:
   - Tests are designed to stay under rate limits
   - If hitting limits, wait for reset time shown in headers

4. **Permission Errors**:
   - Ensure test users have `azure:read` role minimum
   - Admin tests require `azure:admin` role

## Expected Test Results

- All authentication tests should pass when `REQUIRE_AUTH=true`
- API endpoint tests will show 403 if user lacks proper roles
- Rate limiting tests verify headers are present
- Swagger UI and OpenAPI schema should always be accessible

## Troubleshooting

If tests fail:
1. Check service logs: `docker compose logs azure-rm-proxy`
2. Verify traefik routing: `docker compose logs traefik`
3. Test direct API access: `curl https://arm-proxy.maltacentral.com/api/ping`
4. Check authentication: Get token from identity provider and test manually