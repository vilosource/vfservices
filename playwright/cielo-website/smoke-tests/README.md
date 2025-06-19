# Cielo Website Smoke Tests

This directory contains Playwright smoke tests for the Cielo website at cielo.viloforge.com.

## Test Coverage

The test suite (`test_cielo_index.py`) includes:

1. **Basic Connectivity Test** (`test_access_cielo_homepage`)
   - Verifies cielo.viloforge.com is accessible
   - Checks for 200 status response
   - Captures page title
   - Takes a screenshot for debugging

2. **HTTPS Redirect Test** (`test_cielo_traefik_redirect`)
   - Confirms Traefik properly redirects HTTP to HTTPS
   - Verifies the domain remains correct after redirect

3. **Content Loading Test** (`test_cielo_page_content`)
   - Ensures the page has actual HTML content
   - Verifies body content exists
   - Checks for navigation elements
   - Looks for main content areas
   - Reports content length

4. **Static Assets Test** (`test_cielo_static_assets`)
   - Monitors all network requests
   - Reports failed asset loads
   - Counts CSS, JavaScript files, and images
   - Validates that static resources load properly

5. **Authentication Redirect Test** (`test_cielo_authentication_redirect`)
   - Checks if unauthenticated users are redirected to login
   - Verifies login form elements if redirected
   - Looks for login links if not redirected
   - Takes screenshot of the authentication state

6. **Responsive Design Test** (`test_cielo_responsive_design`)
   - Tests three viewport sizes: Desktop (1920x1080), Tablet (768x1024), Mobile (375x667)
   - Checks for mobile menu on smaller viewports
   - Verifies content fits within viewport
   - Takes screenshots for each viewport size

7. **SSL Certificate Test** (`test_cielo_ssl_certificate`)
   - Validates SSL certificate is properly configured
   - Checks certificate covers cielo.viloforge.com domain
   - Verifies certificate issuer and validity dates
   - Reports certificate coverage for troubleshooting

8. **Browser SSL Validation Test** (`test_ssl_certificate_in_browser`)
   - Tests certificate acceptance in real browser context
   - Distinguishes between valid certificates and self-signed
   - Provides clear error messages for certificate issues

9. **Full Login/Logout Flow Test** (`test_cielo_full_login_logout_flow`)
   - Complete authentication workflow test
   - Login as user 'alice' with password 'alice123'
   - Verifies CIELO branding throughout the flow
   - Validates dashboard access after login
   - Tests logout functionality and confirmation
   - Confirms session is properly cleared
   - Takes screenshots at each step for debugging

## Prerequisites

1. Install dependencies from the parent directory:
```bash
cd ../../  # Go to playwright directory
pip install -r requirements.txt
playwright install chromium
```

## Running the Tests

### Run all Cielo website tests:
```bash
# From the playwright directory
pytest cielo-website/smoke-tests/

# Or directly
pytest cielo-website/smoke-tests/test_cielo_index.py
```

### Run with verbose output:
```bash
pytest -v cielo-website/smoke-tests/test_cielo_index.py
```

### Run specific test:
```bash
pytest cielo-website/smoke-tests/test_cielo_index.py::test_access_cielo_homepage
```

### Run as standalone script:
```bash
python cielo-website/smoke-tests/test_cielo_index.py
```

### Run only the login/logout test:
```bash
pytest cielo-website/smoke-tests/test_cielo_index.py::test_cielo_full_login_logout_flow -v
```

### Run with visible browser (headed mode):
```bash
pytest cielo-website/smoke-tests/test_cielo_index.py --headed
```

## Expected Results

- Tests should pass when the Cielo website service is running correctly
- Multiple screenshots are saved for debugging:
  - `cielo_homepage.png` - Main page screenshot
  - `cielo_auth_check.png` - Authentication state screenshot
  - `cielo_desktop_view.png` - Desktop viewport
  - `cielo_tablet_view.png` - Tablet viewport
  - `cielo_mobile_view.png` - Mobile viewport
  - `cielo_alice_login_form.png` - Login form with credentials filled
  - `cielo_alice_logged_in.png` - Dashboard after successful login
  - `cielo_alice_logout_confirm.png` - Logout confirmation page
  - `cielo_alice_after_logout.png` - After logout completion
  - `cielo_alice_error.png` - Captured if any test fails

## Test User Credentials

The login test uses the following test account:
- Username: `alice`
- Password: `alice123`

This user should exist in the identity provider with appropriate permissions.

### Important: CIELO Access Permission

The CIELO website requires users to have the `cielo.access` permission. Without this permission, authenticated users are redirected to the main VF Services site (www.vfservices.viloforge.com).

To grant this permission:
1. Access the Django admin panel
2. Find the user 'alice'
3. Add the `cielo.access` permission
4. Save the user

Alternatively, use a Django management command:
```python
from django.contrib.auth.models import User, Permission
user = User.objects.get(username='alice')
permission = Permission.objects.get(codename='access', content_type__app_label='cielo')
user.user_permissions.add(permission)
```

## Troubleshooting

1. **DNS Resolution Errors**: If you get DNS errors for cielo.viloforge.com, ensure the domain is properly configured
2. **Certificate Errors**: 
   - For self-signed certificates, tests use `ignore_https_errors=True`
   - For production, run `make cert` to obtain valid Let's Encrypt certificates
   - Certificate should cover both `*.vfservices.viloforge.com` and `*.cielo.viloforge.com`
3. **Timeouts**: Increase wait times if services are slow to respond
4. **Authentication**: The Cielo website requires authentication through the identity provider
5. **Login Issues**:
   - Ensure SSO_COOKIE_DOMAIN is set to `.viloforge.com` in docker-compose.yml
   - Verify JWT cookie is being set correctly
   - Check that the identity provider is running
6. **Logout Not Working**: 
   - Verify cookie deletion includes all parameters (domain, path, secure, httponly)
   - Check browser console for any JavaScript errors

## Notes

- Tests access the service through Traefik endpoints as specified in CLAUDE.md
- The Cielo website is configured with `APPLICATION_SET_DOMAIN=cielo.viloforge.com`
- Authentication is handled through the shared identity provider
- Static assets are served from the `/static/` path
- The website shares authentication with VF Services through JWT cookies on `.viloforge.com` domain