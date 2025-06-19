# Website Smoke Tests

This directory contains Playwright smoke tests for the main website service at vfservices.viloforge.com.

## Test Coverage

The test suite (`test_vfservices_access.py`) includes:

1. **Basic Connectivity Test** (`test_access_vfservices_homepage`)
   - Verifies vfservices.viloforge.com is accessible
   - Checks for 200 status response
   - Takes a screenshot for debugging

2. **HTTPS Redirect Test** (`test_check_traefik_redirect`)
   - Confirms Traefik properly redirects HTTP to HTTPS
   - Verifies the domain remains correct after redirect

3. **Content Loading Test** (`test_check_page_content`)
   - Ensures the page has actual HTML content
   - Verifies body content exists
   - Reports content length

4. **Static Assets Test** (`test_check_static_assets`)
   - Monitors all network requests
   - Reports failed asset loads
   - Counts CSS and JavaScript files

5. **Full Login/Logout Flow Test** (`test_full_login_logout_flow`)
   - Tests complete authentication flow with user alice/alice123
   - Verifies redirect to login page when not authenticated
   - Fills in and submits login form
   - Confirms successful login and redirect
   - Navigates to logout page
   - Clicks "Yes, Logout" confirmation button
   - Verifies logout completion
   - Takes screenshots at each step for debugging:
     - `website_alice_login_form.png` - Login form filled
     - `website_alice_logged_in.png` - After successful login
     - `website_alice_logout_confirm.png` - Logout confirmation page
     - `website_alice_after_logout.png` - After logout
   - **Note**: Currently detects that JWT cookies persist after logout, which may need to be addressed

## Prerequisites

1. Install dependencies from the parent directory:
```bash
cd ../../  # Go to playwright directory
pip install -r requirements.txt
playwright install chromium
```

## Running the Tests

### Run all website tests:
```bash
# From the playwright directory
pytest website/smoke-tests/

# Or directly
pytest website/smoke-tests/test_vfservices_access.py
```

### Run with verbose output:
```bash
pytest -v website/smoke-tests/test_vfservices_access.py
```

### Run specific test:
```bash
pytest website/smoke-tests/test_vfservices_access.py::test_access_vfservices_homepage
```

### Run as standalone script:
```bash
python website/smoke-tests/test_vfservices_access.py
```

## Expected Results

- All tests should pass when the website service is running correctly
- Screenshots are saved as `vfservices_homepage.png` for debugging
- The website should redirect to the login page at `/accounts/login/`

## Troubleshooting

1. **500 Errors**: If you encounter 500 errors, check that the `APPLICATION_SET_DOMAIN` is properly configured in the settings
2. **Certificate Errors**: Tests use `ignore_https_errors=True` to handle self-signed certificates
3. **Timeouts**: Increase wait times if services are slow to respond

## Notes

- Tests access the service through Traefik endpoints as specified in CLAUDE.md
- The main website handles authentication through the identity provider
- Static assets are served from the `/static/` path