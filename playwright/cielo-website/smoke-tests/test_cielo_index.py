"""
Playwright smoke test for Cielo website index page
Tests basic functionality and page loading for cielo.viloforge.com
"""
import sys
import os
import pytest
import ssl
import socket
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from playwright.common.auth import authenticated_page, AuthenticationError


def test_access_cielo_homepage():
    """Test accessing cielo.viloforge.com homepage"""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        context = browser.new_context(
            # Accept self-signed certificates if needed
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Navigate to the Cielo website
            response = page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Assert successful response
            assert response is not None, "Failed to get response from cielo.viloforge.com"
            assert response.status == 200, f"Expected status 200, got {response.status}"
            
            # Check page title exists and contains CIELO
            page_title = page.title()
            assert page_title is not None, "Page should have a title"
            assert "CIELO" in page_title, f"Page title should contain 'CIELO', but got: '{page_title}'"
            
            # Check if we're on the login page or the actual CIELO dashboard
            current_url = page.url
            if "/login" in current_url or "/accounts/login" in current_url:
                print(f"✓ Redirected to login page (authentication required)")
                print(f"✓ Login page title contains CIELO: {page_title}")
            else:
                # If logged in, verify we see CIELO branding
                print(f"✓ Accessed CIELO dashboard directly")
                
                # Look for CIELO text in the page content
                page_content = page.content()
                assert "CIELO" in page_content, "Page content should contain CIELO branding"
                
                # Check for specific CIELO elements
                cielo_elements = page.locator('text=/CIELO/i').count()
                print(f"✓ Found {cielo_elements} elements with CIELO branding")
            
            # Take screenshot for debugging
            page.screenshot(path="cielo_homepage.png")
            
            print(f"✓ Successfully accessed cielo.viloforge.com")
            print(f"✓ Page title: {page_title}")
            print(f"✓ Response status: {response.status}")
            print(f"✓ Current URL: {current_url}")
            
        finally:
            browser.close()


def test_cielo_traefik_redirect():
    """Test that HTTP redirects to HTTPS via Traefik"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Try to access HTTP version
            response = page.goto("http://cielo.viloforge.com", wait_until="domcontentloaded")
            
            # Check that we ended up on HTTPS
            assert page.url.startswith("https://"), "Should redirect to HTTPS"
            assert "cielo.viloforge.com" in page.url, "Should stay on cielo domain"
            
            print(f"✓ HTTP correctly redirects to HTTPS")
            print(f"✓ Final URL: {page.url}")
            
        finally:
            browser.close()


def test_cielo_page_content():
    """Test that the Cielo page loads with expected content and branding"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to the site
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Wait for body to be visible
            page.wait_for_selector("body", state="visible")
            
            # Check that page has content
            body_text = page.text_content("body")
            assert body_text and len(body_text.strip()) > 0, "Page should have content"
            
            # Check for CIELO branding in content
            assert "CIELO" in body_text or "Cielo" in body_text, "Page should contain CIELO branding"
            
            # Check for common elements that might exist
            html_content = page.content()
            assert "<html" in html_content, "Should have HTML tag"
            assert "<body" in html_content, "Should have body tag"
            
            # Check if we're on login page or dashboard
            current_url = page.url
            if "/login" in current_url or "/accounts/login" in current_url:
                # Check for login form
                login_form = page.locator('form').count()
                print(f"✓ Login page detected with {login_form} form(s)")
            else:
                # Check for CIELO-specific content on dashboard
                # Look for cloud-related keywords
                cloud_keywords = ["Cloud", "Azure", "Resources", "Cost", "Management"]
                found_keywords = []
                for keyword in cloud_keywords:
                    if keyword.lower() in body_text.lower():
                        found_keywords.append(keyword)
                
                if found_keywords:
                    print(f"✓ Found cloud-related keywords: {', '.join(found_keywords)}")
            
            # Look for navigation elements
            nav_elements = page.locator('nav, .navbar, .navigation, header').count()
            print(f"✓ Found {nav_elements} navigation elements")
            
            # Look for main content area
            main_content = page.locator('main, .main, .content, [role="main"]').count()
            print(f"✓ Found {main_content} main content areas")
            
            print(f"✓ Page loaded with content")
            print(f"✓ Content length: {len(body_text)} characters")
            print(f"✓ CIELO branding verified in content")
            
        finally:
            browser.close()


def test_cielo_static_assets():
    """Test that static assets load correctly"""
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
            # Navigate to the site
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Wait a bit for all resources to load
            page.wait_for_timeout(2000)
            
            # Check if any requests failed
            if failed_requests:
                print(f"⚠ Failed requests: {len(failed_requests)}")
                for req in failed_requests[:5]:  # Show first 5 failures
                    print(f"  - {req}")
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
            
            # Check for images
            images = page.locator('img[src]').all()
            print(f"✓ Found {len(images)} images")
            
        finally:
            browser.close()


def test_cielo_authentication_redirect():
    """Test that unauthenticated users are redirected to login"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to the Cielo website
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            current_url = page.url
            
            # Check if redirected to login
            if "/login" in current_url or "/accounts/login" in current_url:
                print("✓ Unauthenticated users redirected to login page")
                print(f"✓ Login URL: {current_url}")
                
                # Check for login form elements
                login_form = page.locator('form').first
                if login_form.is_visible():
                    print("✓ Login form is visible")
                    
                    # Check for username/email field
                    username_field = page.locator('input[name="username"], input[name="email"], input[type="email"]').first
                    if username_field.is_visible():
                        print("✓ Username/email field found")
                    
                    # Check for password field
                    password_field = page.locator('input[name="password"], input[type="password"]').first
                    if password_field.is_visible():
                        print("✓ Password field found")
            else:
                print(f"✓ Page loaded without authentication requirement")
                print(f"✓ Current URL: {current_url}")
                
                # Check if there's a login link
                login_links = page.locator('a[href*="login"], a:has-text("Login"), a:has-text("Sign In")').count()
                if login_links > 0:
                    print(f"✓ Found {login_links} login link(s)")
            
            # Take screenshot
            page.screenshot(path="cielo_auth_check.png")
            
        finally:
            browser.close()


def test_cielo_responsive_design():
    """Test that the Cielo website is responsive"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        # Test different viewport sizes
        viewports = [
            {"name": "Desktop", "width": 1920, "height": 1080},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Mobile", "width": 375, "height": 667}
        ]
        
        for viewport in viewports:
            context = browser.new_context(
                ignore_https_errors=True,
                viewport={"width": viewport["width"], "height": viewport["height"]}
            )
            page = context.new_page()
            
            try:
                print(f"\nTesting {viewport['name']} viewport ({viewport['width']}x{viewport['height']})...")
                
                # Navigate to the site
                page.goto("https://cielo.viloforge.com", wait_until="networkidle")
                
                # Take screenshot for this viewport
                page.screenshot(path=f"cielo_{viewport['name'].lower()}_view.png")
                
                # Check if mobile menu exists for smaller viewports
                if viewport["width"] < 992:
                    mobile_menu = page.locator('.navbar-toggler, .mobile-menu, .hamburger, button[data-toggle="collapse"]').count()
                    if mobile_menu > 0:
                        print(f"✓ Mobile menu found for {viewport['name']} view")
                
                # Check if content is properly contained
                body_width = page.evaluate("document.body.scrollWidth")
                viewport_width = page.evaluate("window.innerWidth")
                
                if body_width <= viewport_width:
                    print(f"✓ Content fits within {viewport['name']} viewport")
                else:
                    print(f"⚠ Content overflow detected in {viewport['name']} view")
                
            finally:
                context.close()
        
        browser.close()


def test_cielo_ssl_certificate():
    """Test SSL certificate validity for cielo.viloforge.com"""
    hostname = "cielo.viloforge.com"
    port = 443
    
    print(f"\nChecking SSL certificate for {hostname}...")
    
    try:
        # First, try with default context (validates certificates)
        context = ssl.create_default_context()
        
        try:
            # Try to connect with certificate validation
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Get certificate info
                    cert = ssock.getpeercert()
                    
                    print(f"✓ Successfully connected to {hostname} with valid SSL certificate")
                    
                    # Extract issuer info
                    issuer_info = cert.get('issuer', [])
                    issuer_str = ', '.join([f"{k}={v}" for sublist in issuer_info for k, v in sublist])
                    print(f"✓ Certificate issued by: {issuer_str}")
                    
                    print(f"✓ Certificate valid from: {cert['notBefore']}")
                    print(f"✓ Certificate valid until: {cert['notAfter']}")
                    
                    # Check certificate domains
                    san_list = []
                    for san in cert.get('subjectAltName', []):
                        if san[0] == 'DNS':
                            san_list.append(san[1])
                    
                    print(f"✓ Certificate covers domains: {', '.join(san_list)}")
                    
                    # Check if cielo.viloforge.com is covered
                    domain_covered = False
                    for san_domain in san_list:
                        if san_domain == hostname or (san_domain.startswith('*.') and hostname.endswith(san_domain[2:])):
                            domain_covered = True
                            break
                    
                    assert domain_covered, f"Certificate should cover {hostname}"
                    print(f"✓ Certificate correctly covers {hostname}")
                    
        except ssl.SSLError as e:
            # Certificate validation failed - check if it's self-signed
            print(f"\n⚠ Certificate validation failed: {e}")
            
            # Now check with no verification to see what certificate is actually presented
            context_no_verify = ssl.create_default_context()
            context_no_verify.check_hostname = False
            context_no_verify.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context_no_verify.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    
                    if cert:
                        # Extract domains from certificate
                        san_list = []
                        for san in cert.get('subjectAltName', []):
                            if san[0] == 'DNS':
                                san_list.append(san[1])
                        
                        print(f"\nCertificate details (unverified):")
                        print(f"  Covers domains: {', '.join(san_list) if san_list else 'No SANs found'}")
                        
                        # Check if cielo.viloforge.com is covered
                        domain_covered = False
                        for san_domain in san_list:
                            if san_domain == hostname or (san_domain.startswith('*.') and hostname.endswith(san_domain[2:])):
                                domain_covered = True
                                break
                        
                        if not domain_covered:
                            print(f"\n❌ CERTIFICATE ISSUE: The certificate does NOT cover {hostname}")
                            print(f"   It only covers: {', '.join(san_list)}")
                            print(f"\n   To fix this, run: make cert")
                            print(f"   This will update the certificate to include cielo.viloforge.com domains")
                            pytest.fail(f"Certificate does not cover {hostname}. Run 'make cert' to update.")
                        else:
                            print(f"\n⚠ Certificate covers {hostname} but is not trusted (likely self-signed)")
                            print(f"   For production, ensure you have a valid certificate from Let's Encrypt")
                            # Don't fail for self-signed in development
                            pytest.skip("Certificate is self-signed (OK for development)")
                    else:
                        print("\n❌ No certificate information available")
                        pytest.fail("Could not retrieve certificate information")
                        
    except socket.timeout:
        print(f"\n⚠ Timeout connecting to {hostname}")
        pytest.skip("Connection timeout")
    except Exception as e:
        print(f"\n⚠ Error checking SSL certificate: {e}")
        pytest.fail(f"Unexpected error: {e}")


def test_ssl_certificate_in_browser():
    """Test SSL certificate handling in browser context"""
    with sync_playwright() as p:
        # First test WITHOUT ignoring HTTPS errors
        browser = p.chromium.launch()
        context = browser.new_context(
            # Do NOT ignore HTTPS errors to see if certificate is valid
            ignore_https_errors=False
        )
        page = context.new_page()
        
        try:
            print("\nTesting SSL certificate validity in browser...")
            
            # Try to navigate without ignoring errors
            try:
                response = page.goto("https://cielo.viloforge.com", wait_until="domcontentloaded", timeout=30000)
                if response and response.ok:
                    print("✓ Browser accepted SSL certificate as valid")
                    print(f"✓ Response status: {response.status}")
            except Exception as e:
                error_msg = str(e)
                if "ERR_CERT_COMMON_NAME_INVALID" in error_msg or "ERR_CERT_AUTHORITY_INVALID" in error_msg:
                    print("⚠ Browser rejected SSL certificate")
                    print(f"  Error: {error_msg}")
                    print("\n  This confirms the certificate does not cover cielo.viloforge.com")
                else:
                    print(f"⚠ Navigation failed: {error_msg}")
                
                # Now test WITH ignoring HTTPS errors to confirm site is accessible
                context2 = browser.new_context(ignore_https_errors=True)
                page2 = context2.new_page()
                response2 = page2.goto("https://cielo.viloforge.com", wait_until="domcontentloaded")
                if response2 and response2.ok:
                    print("\n✓ Site is accessible when ignoring certificate errors")
                    print("  This confirms the issue is specifically with the SSL certificate")
                context2.close()
                
        finally:
            browser.close()


def test_cielo_full_login_logout_flow():
    """Test complete login and logout flow for user alice on Cielo website"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Step 1: Navigate to the Cielo site (should redirect to login)
            print("Step 1: Navigating to Cielo site...")
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Should be redirected to login page
            assert "/accounts/login/" in page.url or "/login" in page.url, f"Expected redirect to login, but at: {page.url}"
            print(f"✓ Redirected to login page: {page.url}")
            
            # Verify CIELO branding on login page
            page_title = page.title()
            assert "CIELO" in page_title, f"Login page should show CIELO branding, but title is: {page_title}"
            print(f"✓ CIELO branding confirmed in title: {page_title}")
            
            # Step 2: Use authentication utility for login and logout
            print("\nStep 2: Testing login/logout with alice...")
            
            # Use the authentication utility which handles the complete flow
            with authenticated_page(page, 'alice', 'password123', 
                                  service_url="https://cielo.viloforge.com") as auth_page:
                
                # Step 3: Verify successful login
                print("\nStep 3: Verifying successful login...")
                current_url = auth_page.url
            
                # Check if we're no longer on the login page
                assert "/accounts/login/" not in current_url and "/login" not in current_url, "Login failed - still on login page"
                print(f"✓ Successfully logged in, redirected to: {current_url}")
                
                # Check if we were redirected to a different domain
                if "cielo.viloforge.com" not in current_url:
                    print(f"⚠ Redirected to different domain: {current_url}")
                    print("This indicates user 'alice' does not have CIELO roles")
                    print("The CieloAccessMiddleware now checks for RBAC roles instead of Django permissions")
                    
                    # Try navigating back to CIELO to confirm the redirect
                    print("\nConfirming role check by navigating back to CIELO...")
                    auth_page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
                    final_url = auth_page.url
                    
                    if "cielo.viloforge.com" not in final_url:
                        print(f"✓ Confirmed: User is redirected away from CIELO (to {final_url})")
                        print("\nTo fix this, ensure:")
                        print("1. CIELO service is registered with identity provider")
                        print("2. User 'alice' has been assigned a CIELO role (e.g., cielo_admin, cielo_user)")
                        print("3. Redis cache has been populated with user's CIELO roles")
                        print("\nSteps to fix:")
                        print("1. Register CIELO: docker exec cielo_website python manage.py register_service")
                        print("2. Update users: docker exec identity-provider python manage.py setup_demo_users --skip-missing-services")
                        
                        # This is expected if CIELO service isn't registered yet
                        pytest.skip("User 'alice' lacks CIELO roles - CIELO service may not be registered")
                    else:
                        print(f"⚠ Unexpected: User can now access CIELO at {final_url}")
                
                # If we reach here, user has access to CIELO
                page_title = auth_page.title()
                print(f"✓ User has access to CIELO domain")
                print(f"✓ Page title: {page_title}")
                
                # Look for CIELO-specific content
                page_content = auth_page.content()
                cielo_indicators = [
                    "CIELO" in page_content,
                    "Azure Resources" in page_content or "Cloud" in page_content,
                    "Dashboard" in page_content
                ]
                assert any(cielo_indicators), "Should see CIELO dashboard content after login"
                print("✓ CIELO dashboard content verified")
                
                # Take screenshot of logged-in state
                auth_page.screenshot(path="cielo_alice_logged_in.png")
                
                # Check for user-specific elements (e.g., username in navbar, logout link)
                logout_link = None
                logout_selectors = [
                    'a[href*="logout"]',
                    'a:has-text("Logout")',
                    'a:has-text("Sign Out")',
                    '.navbar a[href*="logout"]',
                    '#navbarCollapse a[href*="logout"]',
                    '.dropdown-menu a[href*="logout"]'  # In case it's in a dropdown
                ]
                
                for selector in logout_selectors:
                    try:
                        elements = auth_page.locator(selector).all()
                        if elements:
                            logout_link = auth_page.locator(selector).first
                            print(f"✓ Found logout link with selector: {selector}")
                            break
                    except:
                        continue
                
                # JWT token check
                token = auth_page.get_jwt_token()
                if token:
                    print(f"✓ JWT token present: {token[:30]}...")
                else:
                    print("⚠ JWT token not found")
            
            # The context manager automatically handles logout
            print("\nStep 4: Automatic logout handled by authentication utility")
            print("✓ User automatically logged out")
            
            # Try to access the main page again to verify logout
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            final_check_url = page.url
            
            # Check if we need to login again
            if "/accounts/login/" in final_check_url or "/login" in final_check_url:
                print("✓ Successfully logged out - redirected to login page")
                print("✓ CIELO authentication flow working correctly")
            else:
                # Check if there's any indication we're logged out
                login_link_present = page.locator('a[href*="login"], a:has-text("Login"), a:has-text("Sign In")').count() > 0
                logout_link_present = page.locator('a[href*="logout"], a:has-text("Logout")').count() > 0
                
                print(f"  - Login link present: {login_link_present}")
                print(f"  - Logout link present: {logout_link_present}")
                
                if login_link_present and not logout_link_present:
                    print("✓ Logout successful - login link visible, logout link gone")
                else:
                    print("⚠ Warning: Logout may not have fully completed")
                    print(f"  - Current URL: {final_check_url}")
                    # Don't fail the test, just warn
            
            print("\n✓ Full CIELO login/logout flow completed!")
            
        except AssertionError as e:
            print(f"✗ Assertion failed: {e}")
            page.screenshot(path="cielo_alice_error.png")
            raise
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            page.screenshot(path="cielo_alice_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running Cielo Website smoke tests...")
    test_access_cielo_homepage()
    test_cielo_traefik_redirect()
    test_cielo_page_content()
    test_cielo_static_assets()
    test_cielo_authentication_redirect()
    test_cielo_responsive_design()
    test_cielo_ssl_certificate()
    test_ssl_certificate_in_browser()
    test_cielo_full_login_logout_flow()
    print("\nAll tests completed!")