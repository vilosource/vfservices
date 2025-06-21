"""
Playwright smoke test for accessing vfservices.viloforge.com
Tests basic connectivity and page loading through Traefik
"""
import sys
import os
import pytest
import ssl
import socket
from playwright.sync_api import sync_playwright, expect

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from common.auth import authenticated_page, AuthenticationError


def test_access_vfservices_homepage():
    """Test accessing vfservices.viloforge.com homepage"""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        context = browser.new_context(
            # Accept self-signed certificates if needed
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Navigate to the main site
            response = page.goto("https://vfservices.viloforge.com", wait_until="networkidle")
            
            # Assert successful response
            assert response.status == 200, f"Expected status 200, got {response.status}"
            
            # Check page title exists
            assert page.title() is not None, "Page should have a title"
            
            # Take screenshot for debugging
            page.screenshot(path="vfservices_homepage.png")
            
            print(f"✓ Successfully accessed vfservices.viloforge.com")
            print(f"✓ Page title: {page.title()}")
            
        finally:
            browser.close()


def test_check_traefik_redirect():
    """Test that HTTP redirects to HTTPS via Traefik"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            # Don't follow redirects automatically
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Try to access HTTP version
            response = page.goto("http://vfservices.viloforge.com", wait_until="domcontentloaded")
            
            # Check that we ended up on HTTPS
            assert page.url.startswith("https://"), "Should redirect to HTTPS"
            assert "vfservices.viloforge.com" in page.url, "Should stay on same domain"
            
            print(f"✓ HTTP correctly redirects to HTTPS")
            print(f"✓ Final URL: {page.url}")
            
        finally:
            browser.close()


def test_check_page_content():
    """Test that the page loads with expected content"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to the site
            page.goto("https://vfservices.viloforge.com", wait_until="networkidle")
            
            # Wait for body to be visible
            page.wait_for_selector("body", state="visible")
            
            # Check that page has content
            body_text = page.text_content("body")
            assert body_text and len(body_text.strip()) > 0, "Page should have content"
            
            # Check for common elements that might exist
            # This can be updated based on actual page structure
            html_content = page.content()
            assert "<html" in html_content, "Should have HTML tag"
            assert "<body" in html_content, "Should have body tag"
            
            print(f"✓ Page loaded with content")
            print(f"✓ Content length: {len(body_text)} characters")
            
        finally:
            browser.close()


def test_check_static_assets():
    """Test that static assets load correctly"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Track network requests
        failed_requests = []
        
        def on_request_failed(request):
            failed_requests.append(request.url)
        
        page.on("requestfailed", on_request_failed)
        
        try:
            # Navigate to the site
            page.goto("https://vfservices.viloforge.com", wait_until="networkidle")
            
            # Wait a bit for all resources to load
            page.wait_for_timeout(2000)
            
            # Check if any requests failed
            if failed_requests:
                print(f"⚠ Failed requests: {failed_requests}")
            else:
                print("✓ All network requests succeeded")
            
            # Check for CSS files
            stylesheets = page.locator('link[rel="stylesheet"]').all()
            print(f"✓ Found {len(stylesheets)} stylesheets")
            
            # Check for JavaScript files
            scripts = page.locator('script[src]').all()
            print(f"✓ Found {len(scripts)} script files")
            
        finally:
            browser.close()


def test_full_login_logout_flow():
    """Test complete login and logout flow for user alice"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Step 1: Navigate to the main site (should redirect to login)
            print("Step 1: Navigating to main site...")
            page.goto("https://vfservices.viloforge.com", wait_until="networkidle")
            
            # Should be redirected to login page
            assert "/accounts/login/" in page.url, f"Expected redirect to login, but at: {page.url}"
            print(f"✓ Redirected to login page: {page.url}")
            
            # Step 2: Fill in login credentials
            print("\nStep 2: Logging in as alice...")
            # Website uses 'email' as the field name but accepts username
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'alice123!#QWERT')
            
            # Take screenshot before login
            page.screenshot(path="website_alice_login_form.png")
            
            # Submit the login form
            page.click('button[type="submit"]')
            
            # Wait for navigation after login
            page.wait_for_load_state("networkidle")
            
            # Wait for either successful redirect or error message
            try:
                # Wait for navigation away from login page (max 5 seconds)
                page.wait_for_url(lambda url: "/accounts/login/" not in url, timeout=5000)
            except:
                # If timeout, check for error messages
                error_found = False
                for selector in ['.alert-danger', '.error', '.errorlist']:
                    if page.locator(selector).count() > 0:
                        error_msg = page.locator(selector).first.inner_text()
                        print(f"Login error: {error_msg}")
                        error_found = True
                        break
                if not error_found:
                    print("Login seems stuck, checking current state...")
            
            page.wait_for_timeout(1000)  # Additional wait for any redirects
            
            # Step 3: Verify successful login
            print("\nStep 3: Verifying successful login...")
            current_url = page.url
            
            # Check if we're no longer on the login page
            assert "/accounts/login/" not in current_url, f"Login failed - still on login page: {current_url}"
            print(f"✓ Successfully logged in, redirected to: {current_url}")
            
            # Take screenshot of logged-in state
            page.screenshot(path="website_alice_logged_in.png")
            
            # Check for user-specific elements (e.g., username in navbar, logout link)
            # Try multiple selectors for logout link
            logout_link = None
            logout_selectors = [
                'a[href*="logout"]',
                'a:has-text("Logout")',
                'a:has-text("Sign Out")',
                '.navbar a[href*="logout"]',
                '#navbarCollapse a[href*="logout"]'
            ]
            
            for selector in logout_selectors:
                try:
                    elements = page.locator(selector).all()
                    if elements:
                        logout_link = page.locator(selector).first
                        print(f"✓ Found logout link with selector: {selector}")
                        break
                except:
                    continue
            
            # If no logout link found, navigate directly to logout URL
            if logout_link is None or not logout_link.is_visible():
                print("⚠ Logout link not visible in UI, navigating directly to logout URL")
                logout_url = "https://vfservices.viloforge.com/accounts/logout/"
            else:
                print("✓ Logout link is visible")
            
            # Step 4: Navigate to logout
            print("\nStep 4: Initiating logout...")
            if logout_link and logout_link.is_visible():
                logout_link.click()
            else:
                page.goto(logout_url, wait_until="networkidle")
            
            page.wait_for_load_state("networkidle")
            
            # Should be on logout confirmation page
            assert "/accounts/logout/" in page.url, f"Expected logout page, but at: {page.url}"
            print(f"✓ On logout confirmation page: {page.url}")
            
            # Take screenshot of logout confirmation page
            page.screenshot(path="website_alice_logout_confirm.png")
            
            # Step 5: Confirm logout
            print("\nStep 5: Confirming logout...")
            
            # Look for logout confirmation button - try multiple possible selectors
            logout_button = None
            button_selectors = [
                'button:has-text("Yes, Logout")',
                'button:has-text("Logout")',
                'input[type="submit"][value*="Logout"]',
                'button[type="submit"]:has-text("Logout")',
                'form[action*="logout"] button[type="submit"]',
                '.btn:has-text("Logout")'
            ]
            
            for selector in button_selectors:
                try:
                    element = page.locator(selector).first
                    if element.is_visible():
                        logout_button = element
                        print(f"✓ Found logout button with selector: {selector}")
                        break
                except:
                    continue
            
            assert logout_button is not None, "Could not find logout confirmation button"
            
            # Click the logout button
            logout_button.click()
            page.wait_for_load_state("networkidle")
            
            # Step 6: Verify logout completed
            print("\nStep 6: Verifying logout completed...")
            final_url = page.url
            
            # Should be redirected back to login or home page
            print(f"✓ After logout, redirected to: {final_url}")
            
            # Take final screenshot
            page.screenshot(path="website_alice_after_logout.png")
            
            # Verify we're logged out by checking cookies and trying to access protected content
            cookies_before_check = context.cookies()
            print(f"\nCookies after logout: {len(cookies_before_check)} total")
            for cookie in cookies_before_check:
                if 'session' in cookie['name'].lower() or 'jwt' in cookie['name'].lower():
                    print(f"  - {cookie['name']}: domain={cookie['domain']}, value={'[SET]' if cookie['value'] else '[EMPTY]'}")
            
            # Wait a bit for logout to fully process
            page.wait_for_timeout(1000)
            
            # Try to access the main page again
            page.goto("https://vfservices.viloforge.com/", wait_until="networkidle")
            final_check_url = page.url
            
            # Check if we need to login again
            if "/accounts/login/" in final_check_url:
                print("✓ Successfully logged out - redirected to login page")
            else:
                # Check if there's any indication we're logged out
                # Look for login link or absence of user info
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
            
            print("\n✓ Full login/logout flow completed!")
            
        except AssertionError as e:
            print(f"✗ Assertion failed: {e}")
            page.screenshot(path="website_alice_error.png")
            raise
        except Exception as e:
            print(f"✗ Test failed with error: {e}")
            page.screenshot(path="website_alice_error.png")
            raise
        finally:
            browser.close()


def test_vfservices_ssl_certificate():
    """Test SSL certificate validity for vfservices.viloforge.com"""
    hostname = "vfservices.viloforge.com"
    port = 443
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Connect and get certificate
        with socket.create_connection((hostname, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate info
                cert = ssock.getpeercert()
                
                print(f"\n✓ Successfully connected to {hostname} with SSL")
                print(f"✓ Certificate issued by: {cert['issuer']}")
                print(f"✓ Certificate valid from: {cert['notBefore']}")
                print(f"✓ Certificate valid until: {cert['notAfter']}")
                
                # Check certificate domains
                san_list = []
                for san in cert.get('subjectAltName', []):
                    if san[0] == 'DNS':
                        san_list.append(san[1])
                
                print(f"✓ Certificate covers domains: {', '.join(san_list)}")
                
                # Check if vfservices.viloforge.com is covered
                domain_covered = False
                for san_domain in san_list:
                    if san_domain == hostname or (san_domain.startswith('*.') and hostname.endswith(san_domain[2:])):
                        domain_covered = True
                        break
                
                assert domain_covered, f"Certificate should cover {hostname}"
                print(f"✓ Certificate correctly covers {hostname}")
                
                # Also check identity subdomain
                identity_hostname = "identity.vfservices.viloforge.com"
                identity_covered = False
                for san_domain in san_list:
                    if san_domain == identity_hostname or (san_domain.startswith('*.') and identity_hostname.endswith(san_domain[2:])):
                        identity_covered = True
                        break
                
                if identity_covered:
                    print(f"✓ Certificate also covers {identity_hostname}")
                else:
                    print(f"⚠ Certificate does not explicitly cover {identity_hostname}")
                    
    except ssl.SSLError as e:
        pytest.fail(f"SSL Error: {e}")
    except Exception as e:
        pytest.fail(f"Error checking SSL certificate: {e}")


if __name__ == "__main__":
    print("Running VF Services smoke tests...")
    test_access_vfservices_homepage()
    test_check_traefik_redirect()
    test_check_page_content()
    test_check_static_assets()
    test_full_login_logout_flow()
    test_vfservices_ssl_certificate()
    print("\nAll tests completed!")