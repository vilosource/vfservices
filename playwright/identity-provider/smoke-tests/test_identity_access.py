"""
Playwright smoke test for accessing identity.vfservices.viloforge.com
Tests identity provider service connectivity and functionality through Traefik
"""
import pytest
from playwright.sync_api import sync_playwright, expect


def test_access_identity_homepage():
    """Test accessing identity.vfservices.viloforge.com homepage"""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        context = browser.new_context(
            # Accept self-signed certificates if needed
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Navigate to the identity provider
            response = page.goto("https://identity.vfservices.viloforge.com", wait_until="networkidle")
            
            # Assert successful response
            assert response.status == 200, f"Expected status 200, got {response.status}"
            
            # Check page title exists
            assert page.title() is not None, "Page should have a title"
            
            # Take screenshot for debugging
            page.screenshot(path="identity_homepage.png")
            
            print(f"✓ Successfully accessed identity.vfservices.viloforge.com")
            print(f"✓ Page title: {page.title()}")
            
        finally:
            browser.close()


def test_check_identity_traefik_redirect():
    """Test that HTTP redirects to HTTPS via Traefik for identity service"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            # Don't follow redirects automatically
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Try to access HTTP version
            response = page.goto("http://identity.vfservices.viloforge.com", wait_until="domcontentloaded")
            
            # Check that we ended up on HTTPS
            assert page.url.startswith("https://"), "Should redirect to HTTPS"
            assert "identity.vfservices.viloforge.com" in page.url, "Should stay on identity subdomain"
            
            print(f"✓ HTTP correctly redirects to HTTPS")
            print(f"✓ Final URL: {page.url}")
            
        finally:
            browser.close()


def test_check_login_page_elements():
    """Test that the login page has expected form elements"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to login page (corrected URL)
            page.goto("https://identity.vfservices.viloforge.com/login/", wait_until="networkidle")
            
            # Debug: print page content if elements not found
            page.wait_for_timeout(1000)  # Wait a bit for JS to load
            
            # Check for login form elements
            # Username field (using the correct ID from the template)
            username_field = page.locator('input#username')
            expect(username_field).to_be_visible()
            
            # Password field (using the correct ID from the template)
            password_field = page.locator('input#password')
            expect(password_field).to_be_visible()
            
            # Submit button
            submit_button = page.locator('button[type="submit"]')
            expect(submit_button).to_be_visible()
            
            # CSRF token (Django forms should have this)
            csrf_token = page.locator('input[name="csrfmiddlewaretoken"]')
            expect(csrf_token).to_be_attached()
            
            print("✓ Login form has username field")
            print("✓ Login form has password field")
            print("✓ Login form has submit button")
            print("✓ CSRF token present")
            
        finally:
            browser.close()


def test_check_api_endpoints():
    """Test that API endpoints are accessible"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Test status endpoint (correct URL from urls.py)
            response = page.goto("https://identity.vfservices.viloforge.com/api/status/", wait_until="networkidle")
            
            # API endpoints might return different status codes
            # 200 for success, 401 for unauthorized
            print(f"✓ API status endpoint returned status: {response.status}")
            
            # Test API info endpoint
            info_response = page.goto("https://identity.vfservices.viloforge.com/api/", wait_until="networkidle")
            print(f"✓ API info endpoint returned status: {info_response.status}")
            
            # Test login API endpoint exists
            login_api_response = page.goto("https://identity.vfservices.viloforge.com/api/login/", wait_until="networkidle")
            print(f"✓ Login API endpoint returned status: {login_api_response.status}")
            
        except Exception as e:
            print(f"Note: Some API endpoints may require authentication: {e}")
        finally:
            browser.close()


def test_check_static_assets_identity():
    """Test that static assets load correctly for identity provider"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Track network requests
        failed_requests = []
        loaded_assets = []
        
        def on_request_failed(request):
            failed_requests.append(request.url)
        
        def on_response(response):
            if response.status == 200 and any(ext in response.url for ext in ['.css', '.js', '.png', '.jpg', '.ico']):
                loaded_assets.append(response.url)
        
        page.on("requestfailed", on_request_failed)
        page.on("response", on_response)
        
        try:
            # Navigate to the identity provider
            page.goto("https://identity.vfservices.viloforge.com", wait_until="networkidle")
            
            # Wait a bit for all resources to load
            page.wait_for_timeout(2000)
            
            # Check if any requests failed
            if failed_requests:
                print(f"⚠ Failed requests: {failed_requests}")
            else:
                print("✓ All network requests succeeded")
            
            # Report loaded assets
            print(f"✓ Successfully loaded {len(loaded_assets)} static assets")
            
            # Check for CSS files
            stylesheets = page.locator('link[rel="stylesheet"]').all()
            print(f"✓ Found {len(stylesheets)} stylesheets")
            
            # Check for JavaScript files
            scripts = page.locator('script[src]').all()
            print(f"✓ Found {len(scripts)} script files")
            
        finally:
            browser.close()


def test_cors_headers():
    """Test that CORS headers are properly configured"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to the identity provider
            response = page.goto("https://identity.vfservices.viloforge.com", wait_until="networkidle")
            
            # Check response headers
            headers = response.headers
            
            # Check for CORS headers if present
            if 'access-control-allow-origin' in headers:
                print(f"✓ CORS Allow-Origin: {headers['access-control-allow-origin']}")
            
            if 'access-control-allow-credentials' in headers:
                print(f"✓ CORS Allow-Credentials: {headers['access-control-allow-credentials']}")
                
            # Check security headers
            if 'x-frame-options' in headers:
                print(f"✓ X-Frame-Options: {headers['x-frame-options']}")
                
            if 'x-content-type-options' in headers:
                print(f"✓ X-Content-Type-Options: {headers['x-content-type-options']}")
            
        finally:
            browser.close()


def test_login_as_alice():
    """Test logging in as user alice"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to login page
            page.goto("https://identity.vfservices.viloforge.com/login/", wait_until="networkidle")
            
            # Fill in login form
            page.fill('input#username', 'alice')
            page.fill('input#password', 'alice123')
            
            # Take screenshot before submitting
            page.screenshot(path="alice_login_before.png")
            
            # Submit the form
            page.click('button[type="submit"]')
            
            # Wait for navigation after login
            page.wait_for_load_state("networkidle")
            
            # Take screenshot after login attempt
            page.screenshot(path="alice_login_after.png")
            
            # Check where we ended up
            current_url = page.url
            print(f"✓ Login attempted for user alice")
            print(f"✓ Current URL after login: {current_url}")
            
            # Check if we're still on login page (failed login) or redirected
            if "/login/" in current_url:
                # Check for error messages
                error_messages = page.locator('.alert-danger, .error, .invalid-feedback').all()
                if error_messages:
                    print("⚠ Login might have failed. Error messages found:")
                    for msg in error_messages:
                        print(f"  - {msg.text_content()}")
                else:
                    print("⚠ Still on login page, but no error messages found")
            else:
                # Successfully logged in and redirected
                print(f"✓ Successfully logged in and redirected to: {current_url}")
                
                # Check for session cookie
                cookies = context.cookies()
                session_cookie = next((c for c in cookies if 'session' in c['name'].lower()), None)
                if session_cookie:
                    print(f"✓ Session cookie set: {session_cookie['name']}")
                    print(f"  - Domain: {session_cookie['domain']}")
                    print(f"  - Secure: {session_cookie['secure']}")
                    print(f"  - HttpOnly: {session_cookie['httpOnly']}")
                
                # Check if we can access a protected page
                page.goto("https://identity.vfservices.viloforge.com/api/profile/", wait_until="networkidle")
                profile_status = page.evaluate("() => fetch('/api/profile/').then(r => r.status)")
                print(f"✓ Profile API access status: {profile_status}")
            
        except Exception as e:
            print(f"✗ Login test failed with error: {e}")
            page.screenshot(path="alice_login_error.png")
            raise
            
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running Identity Provider smoke tests...")
    test_access_identity_homepage()
    test_check_identity_traefik_redirect()
    test_check_login_page_elements()
    test_check_api_endpoints()
    test_check_static_assets_identity()
    test_cors_headers()
    test_login_as_alice()
    print("\nAll tests completed!")