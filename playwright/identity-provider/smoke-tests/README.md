# Identity Provider Smoke Tests

This directory contains Playwright smoke tests for the Identity Provider service at identity.vfservices.viloforge.com.

## Test Coverage

The test suite (`test_identity_access.py`) includes:

1. **Basic Connectivity Test** (`test_access_identity_homepage`)
   - Verifies identity.vfservices.viloforge.com is accessible
   - Checks for 200 status response
   - Takes a screenshot for debugging

2. **HTTPS Redirect Test** (`test_check_identity_traefik_redirect`)
   - Confirms Traefik properly redirects HTTP to HTTPS
   - Verifies the domain remains correct after redirect

3. **Login Page Elements Test** (`test_check_login_page_elements`)
   - Checks for presence of username field
   - Checks for presence of password field
   - Verifies submit button exists
   - Confirms CSRF token is present (Django security)

4. **API Endpoints Test** (`test_check_api_endpoints`)
   - Tests health check endpoint accessibility
   - Verifies auth API endpoints exist
   - Reports status codes for debugging

5. **Static Assets Test** (`test_check_static_assets_identity`)
   - Monitors all network requests
   - Reports failed asset loads
   - Counts CSS and JavaScript files

6. **CORS Headers Test** (`test_cors_headers`)
   - Checks for proper CORS configuration
   - Verifies security headers are present

7. **Login Test** (`test_login_as_alice`)
   - Tests actual login functionality with user alice/alice123
   - Verifies successful authentication and redirect
   - Checks session cookie is properly set
   - Validates access to protected API endpoints after login
   - Takes screenshots for debugging (alice_login_before.png, alice_login_after.png)

## Prerequisites

1. Install dependencies from the parent directory:
```bash
cd ../../  # Go to playwright directory
pip install -r requirements.txt
playwright install chromium
```

## Running the Tests

### Run all identity provider tests:
```bash
# From the playwright directory
pytest identity-provider/smoke-tests/

# Or directly
pytest identity-provider/smoke-tests/test_identity_access.py
```

### Run with verbose output:
```bash
pytest -v identity-provider/smoke-tests/test_identity_access.py
```

### Run specific test:
```bash
pytest identity-provider/smoke-tests/test_identity_access.py::test_check_login_page_elements
```

### Run as standalone script:
```bash
python identity-provider/smoke-tests/test_identity_access.py
```

## Expected Results

- All tests should pass when the identity provider is running correctly
- Screenshots are saved as `identity_homepage.png` for debugging
- Failed network requests are reported but may not fail the test
- API endpoints may return 401 if authentication is required

## Troubleshooting

1. **Certificate Errors**: Tests use `ignore_https_errors=True` to handle self-signed certificates
2. **Timeouts**: Increase wait times if services are slow to respond
3. **Login Form**: If login form structure changes, update the selectors in `test_check_login_page_elements`

## Notes

- Tests access the service through Traefik endpoints as specified in CLAUDE.md
- The identity provider handles authentication for all VF Services
- CORS headers are important for cross-domain authentication