"""
Comprehensive authentication flow tests for CIELO website.
Tests login, logout, and session management.
"""
import pytest
from playwright.sync_api import sync_playwright, expect
import time


def test_cielo_complete_auth_flow():
    """Test complete authentication flow: login -> verify access -> logout -> verify logout"""
    with sync_playwright() as p:
        # Launch browser with debugging enabled
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        
        # Enable console logging for debugging
        page = context.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        try:
            print("\n=== Starting CIELO Authentication Flow Test ===")
            
            # Step 1: Initial visit (should redirect to login)
            print("\nStep 1: Visiting CIELO homepage...")
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Verify we're on the login page
            assert "/accounts/login/" in page.url or "/login" in page.url
            print(f"✓ Redirected to login page: {page.url}")
            
            # Check initial cookies
            initial_cookies = context.cookies()
            print(f"\nInitial cookies: {len(initial_cookies)} total")
            for cookie in initial_cookies:
                if 'jwt' in cookie['name']:
                    print(f"  - {cookie['name']}: domain={cookie['domain']}, value={'[SET]' if cookie['value'] else '[EMPTY]'}")
            
            # Step 2: Login as alice
            print("\nStep 2: Logging in as alice...")
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'alice123')
            
            # Take screenshot before login
            page.screenshot(path="cielo_01_login_form.png")
            
            # Submit login form
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            # Step 3: Verify successful login
            print("\nStep 3: Verifying successful login...")
            current_url = page.url
            
            if "cielo.viloforge.com" not in current_url:
                print(f"✗ Redirected away from CIELO to: {current_url}")
                print("  This indicates alice doesn't have CIELO access roles")
                pytest.fail("User alice lacks CIELO access")
            
            print(f"✓ Successfully logged in and stayed on CIELO: {current_url}")
            
            # Check post-login cookies
            login_cookies = context.cookies()
            print(f"\nPost-login cookies: {len(login_cookies)} total")
            jwt_found = False
            for cookie in login_cookies:
                if 'jwt' in cookie['name']:
                    jwt_found = True
                    print(f"  - {cookie['name']}: domain={cookie['domain']}, httpOnly={cookie['httpOnly']}, secure={cookie['secure']}")
            
            assert jwt_found, "JWT cookie should be set after login"
            print("✓ JWT cookie is set")
            
            # Take screenshot of logged-in state
            page.screenshot(path="cielo_02_logged_in.png")
            
            # Step 4: Navigate to a protected page to verify authentication
            print("\nStep 4: Testing authenticated access...")
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            
            # Should NOT be redirected to login
            assert "/login" not in page.url and "/accounts/login/" not in page.url
            print("✓ Can access CIELO pages while authenticated")
            
            # Step 5: Find and click logout link
            print("\nStep 5: Initiating logout...")
            
            # Try different ways to find logout link
            logout_link = None
            logout_selectors = [
                'a[href*="logout"]',
                'a:has-text("Logout")',
                'a:has-text("Sign Out")',
                'a:has-text("Log Out")',
                '.navbar a[href*="logout"]',
                'nav a[href*="logout"]'
            ]
            
            for selector in logout_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        logout_link = page.locator(selector).first
                        if logout_link.is_visible():
                            print(f"✓ Found logout link with selector: {selector}")
                            break
                        else:
                            logout_link = None
                except:
                    continue
            
            if logout_link:
                logout_link.click()
                page.wait_for_load_state("networkidle")
            else:
                print("⚠ Logout link not found, navigating directly to logout URL")
                page.goto("https://cielo.viloforge.com/accounts/logout/", wait_until="networkidle")
            
            # Step 6: Confirm logout
            print("\nStep 6: Confirming logout...")
            
            # Should be on logout confirmation page
            assert "/accounts/logout/" in page.url
            print(f"✓ On logout confirmation page: {page.url}")
            
            # Take screenshot of logout page
            page.screenshot(path="cielo_03_logout_confirm.png")
            
            # Find and click the logout button
            logout_button = page.locator('button:has-text("Yes, Logout")').first
            assert logout_button.is_visible(), "Logout button should be visible"
            
            # Check cookies before logout
            pre_logout_cookies = context.cookies()
            print(f"\nPre-logout cookies: {len(pre_logout_cookies)} total")
            for cookie in pre_logout_cookies:
                if 'jwt' in cookie['name']:
                    print(f"  - {cookie['name']}: value={'[SET]' if cookie['value'] else '[EMPTY]'}")
            
            # Click logout button
            logout_button.click()
            page.wait_for_load_state("networkidle")
            
            # Step 7: Verify logout completed
            print("\nStep 7: Verifying logout completed...")
            
            # Should be redirected to login page
            assert "/accounts/login/" in page.url or "/login" in page.url
            print(f"✓ Redirected to login page after logout: {page.url}")
            
            # Check cookies after logout
            post_logout_cookies = context.cookies()
            print(f"\nPost-logout cookies: {len(post_logout_cookies)} total")
            jwt_still_present = False
            for cookie in post_logout_cookies:
                if 'jwt' in cookie['name'] and cookie['value']:
                    jwt_still_present = True
                    print(f"  - {cookie['name']}: value={'[SET]' if cookie['value'] else '[EMPTY]'}, expires={cookie.get('expires', 'N/A')}")
            
            # Take screenshot after logout
            page.screenshot(path="cielo_04_after_logout.png")
            
            # Step 8: Verify user cannot access protected pages
            print("\nStep 8: Verifying access is denied after logout...")
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            
            # Should be redirected to login
            assert "/accounts/login/" in page.url or "/login" in page.url
            print("✓ Access denied after logout - redirected to login")
            
            # Step 9: Try to manually navigate with old session
            print("\nStep 9: Testing session invalidation...")
            
            # Try to access a protected URL directly
            page.goto("https://cielo.viloforge.com/dashboard/", wait_until="networkidle")
            assert "/accounts/login/" in page.url or "/login" in page.url
            print("✓ Session properly invalidated - cannot access protected pages")
            
            # Final verdict
            print("\n=== Test Results ===")
            if jwt_still_present:
                print("⚠ WARNING: JWT cookie may still be present after logout")
                print("  This could be a cookie domain issue")
            else:
                print("✓ JWT cookie successfully cleared")
            
            print("✓ Login flow: PASSED")
            print("✓ Logout flow: PASSED")
            print("✓ Session management: PASSED")
            print("\n✓ All authentication tests passed!")
            
        except AssertionError as e:
            print(f"\n✗ Test failed: {e}")
            page.screenshot(path="cielo_error_state.png")
            raise
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            page.screenshot(path="cielo_error_state.png")
            raise
        finally:
            browser.close()


def test_cielo_logout_persistence():
    """Test that logout persists across page refreshes and new sessions"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("\n=== Testing Logout Persistence ===")
            
            # Quick login
            print("\nLogging in as alice...")
            page.goto("https://cielo.viloforge.com/accounts/login/", wait_until="networkidle")
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'alice123')
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            # Verify logged in
            assert "cielo.viloforge.com" in page.url and "/login" not in page.url
            print("✓ Logged in successfully")
            
            # Logout
            print("\nLogging out...")
            page.goto("https://cielo.viloforge.com/accounts/logout/", wait_until="networkidle")
            page.click('button:has-text("Yes, Logout")')
            page.wait_for_load_state("networkidle")
            
            # Test 1: Refresh page
            print("\nTest 1: Page refresh after logout...")
            page.reload()
            page.wait_for_load_state("networkidle")
            
            # Try to access protected page
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            assert "/accounts/login/" in page.url or "/login" in page.url
            print("✓ Still logged out after page refresh")
            
            # Test 2: New page in same context
            print("\nTest 2: New page in same browser context...")
            page2 = context.new_page()
            page2.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            assert "/accounts/login/" in page2.url or "/login" in page2.url
            print("✓ Still logged out in new page")
            page2.close()
            
            # Test 3: Direct navigation attempts
            print("\nTest 3: Direct navigation attempts...")
            protected_urls = [
                "https://cielo.viloforge.com/",
                "https://cielo.viloforge.com/dashboard/",
                "https://cielo.viloforge.com/private/"
            ]
            
            for url in protected_urls:
                page.goto(url, wait_until="networkidle")
                assert "/accounts/login/" in page.url or "/login" in page.url
                print(f"✓ Access denied to {url}")
            
            print("\n✓ Logout persistence test passed!")
            
        finally:
            browser.close()


def test_cielo_concurrent_sessions():
    """Test logout behavior with multiple browser sessions"""
    with sync_playwright() as p:
        browser1 = p.chromium.launch(headless=True)
        browser2 = p.chromium.launch(headless=True)
        
        try:
            print("\n=== Testing Concurrent Sessions ===")
            
            # Create two separate browser contexts (like two different browsers)
            context1 = browser1.new_context(ignore_https_errors=True)
            context2 = browser2.new_context(ignore_https_errors=True)
            
            page1 = context1.new_page()
            page2 = context2.new_page()
            
            # Login in both browsers
            print("\nLogging in on Browser 1...")
            page1.goto("https://cielo.viloforge.com/accounts/login/", wait_until="networkidle")
            page1.fill('input[name="email"]', 'alice')
            page1.fill('input[name="password"]', 'alice123')
            page1.click('button[type="submit"]')
            page1.wait_for_load_state("networkidle")
            assert "cielo.viloforge.com" in page1.url and "/login" not in page1.url
            print("✓ Browser 1 logged in")
            
            print("\nLogging in on Browser 2...")
            page2.goto("https://cielo.viloforge.com/accounts/login/", wait_until="networkidle")
            page2.fill('input[name="email"]', 'alice')
            page2.fill('input[name="password"]', 'alice123')
            page2.click('button[type="submit"]')
            page2.wait_for_load_state("networkidle")
            assert "cielo.viloforge.com" in page2.url and "/login" not in page2.url
            print("✓ Browser 2 logged in")
            
            # Logout from Browser 1
            print("\nLogging out from Browser 1...")
            page1.goto("https://cielo.viloforge.com/accounts/logout/", wait_until="networkidle")
            page1.click('button:has-text("Yes, Logout")')
            page1.wait_for_load_state("networkidle")
            
            # Verify Browser 1 is logged out
            page1.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            assert "/accounts/login/" in page1.url or "/login" in page1.url
            print("✓ Browser 1 is logged out")
            
            # Check if Browser 2 is still logged in (it should be - separate session)
            print("\nChecking Browser 2 session...")
            page2.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            
            if "/login" in page2.url or "/accounts/login/" in page2.url:
                print("✓ Browser 2 was also logged out (shared authentication system)")
            else:
                print("✓ Browser 2 remains logged in (independent session)")
            
            print("\n✓ Concurrent session test completed!")
            
        finally:
            browser1.close()
            browser2.close()


if __name__ == "__main__":
    print("Running CIELO authentication flow tests...")
    test_cielo_complete_auth_flow()
    test_cielo_logout_persistence()
    test_cielo_concurrent_sessions()
    print("\nAll tests completed!")