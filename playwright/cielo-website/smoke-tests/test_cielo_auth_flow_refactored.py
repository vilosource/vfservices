"""
Refactored version of test_cielo_auth_flow.py using the authentication utility.
This demonstrates how much cleaner and more maintainable the tests become.
"""
import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

import pytest
from playwright.sync_api import sync_playwright, expect
from playwright.common.auth import authenticated_page, AuthenticationError
import time


def test_cielo_complete_auth_flow_refactored():
    """Test complete authentication flow using the auth utility"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        try:
            print("\n=== Starting CIELO Authentication Flow Test (Refactored) ===")
            
            # The entire login/logout flow is now handled by the context manager
            with authenticated_page(page, "alice", service_url="https://cielo.viloforge.com") as auth_page:
                print("✓ Successfully logged in as alice")
                print(f"✓ Current URL: {auth_page.url}")
                
                # Verify we're on CIELO (not redirected away)
                assert "cielo.viloforge.com" in auth_page.url
                assert "/login" not in auth_page.url
                print("✓ Alice has access to CIELO")
                
                # Get JWT token
                token = auth_page.get_jwt_token()
                assert token is not None
                print(f"✓ JWT token confirmed: {token[:30]}...")
                
                # Navigate to a protected page
                auth_page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
                assert "/login" not in auth_page.url
                print("✓ Can access CIELO pages while authenticated")
                
                # Take screenshot if needed
                auth_page.screenshot(path="cielo_refactored_logged_in.png")
            
            # User is automatically logged out here
            print("✓ Automatically logged out")
            
            # Verify logout was successful
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            assert "/accounts/login/" in page.url or "/login" in page.url
            print("✓ Access denied after logout - redirected to login")
            
            print("\n✓ All authentication tests passed!")
            
        finally:
            browser.close()


def test_cielo_access_control_refactored():
    """Test different users' access to CIELO using auth utility"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("\n=== Testing CIELO Access Control (Refactored) ===")
            
            # Test 1: Alice should have access
            print("\nTest 1: Alice's access to CIELO")
            try:
                with authenticated_page(page, "alice", service_url="https://cielo.viloforge.com") as auth_page:
                    assert "cielo.viloforge.com" in auth_page.url
                    print("✓ Alice has access to CIELO")
            except AuthenticationError as e:
                print(f"✗ Alice should have access but got: {e}")
                raise
            
            # Test 2: Admin might not have CIELO access (depends on roles)
            print("\nTest 2: Admin's access to CIELO")
            try:
                with authenticated_page(page, "admin", service_url="https://cielo.viloforge.com") as auth_page:
                    if "cielo.viloforge.com" in auth_page.url and "/login" not in auth_page.url:
                        print("✓ Admin has access to CIELO")
                    else:
                        print("✓ Admin redirected - no CIELO access")
            except AuthenticationError as e:
                if "does not have access" in str(e):
                    print("✓ Admin correctly denied CIELO access")
                else:
                    print(f"✗ Unexpected error: {e}")
            
            print("\n✓ Access control tests completed!")
            
        finally:
            browser.close()


def test_concurrent_cielo_sessions_refactored():
    """Test concurrent sessions using auth utility"""
    with sync_playwright() as p:
        browser1 = p.chromium.launch(headless=True)
        browser2 = p.chromium.launch(headless=True)
        
        try:
            print("\n=== Testing Concurrent CIELO Sessions (Refactored) ===")
            
            context1 = browser1.new_context(ignore_https_errors=True)
            context2 = browser2.new_context(ignore_https_errors=True)
            
            page1 = context1.new_page()
            page2 = context2.new_page()
            
            # Use nested context managers for concurrent sessions
            with authenticated_page(page1, "alice", service_url="https://cielo.viloforge.com") as alice1:
                print("✓ Alice logged in on Browser 1")
                
                with authenticated_page(page2, "alice", service_url="https://cielo.viloforge.com") as alice2:
                    print("✓ Alice logged in on Browser 2")
                    
                    # Both sessions should be active
                    alice1.goto("https://cielo.viloforge.com/")
                    assert "/login" not in alice1.url
                    print("✓ Browser 1 session active")
                    
                    alice2.goto("https://cielo.viloforge.com/")
                    assert "/login" not in alice2.url
                    print("✓ Browser 2 session active")
                
                # Browser 2 logged out
                print("✓ Browser 2 automatically logged out")
                
                # Check if Browser 1 is still active
                alice1.goto("https://cielo.viloforge.com/")
                if "/login" not in alice1.url:
                    print("✓ Browser 1 still logged in (independent session)")
                else:
                    print("✓ Browser 1 also logged out (shared auth system)")
            
            print("✓ Browser 1 automatically logged out")
            print("\n✓ Concurrent session test completed!")
            
        finally:
            browser1.close()
            browser2.close()


def test_jwt_token_management_refactored():
    """Test JWT token extraction and management"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("\n=== Testing JWT Token Management (Refactored) ===")
            
            with authenticated_page(page, "alice") as auth_page:
                # Get JWT token
                token = auth_page.get_jwt_token()
                assert token is not None
                print(f"✓ JWT token extracted: {token[:30]}...")
                
                # Use the token for API calls if needed
                # This demonstrates how you can use the token for API testing
                api_headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                print("✓ Token ready for API calls")
                
                # Navigate to different services while maintaining auth
                services = [
                    "https://website.vfservices.viloforge.com/",
                    "https://cielo.viloforge.com/"
                ]
                
                for service in services:
                    auth_page.goto(service, wait_until="networkidle")
                    if "/login" not in auth_page.url:
                        print(f"✓ Can access {service} with token")
                    else:
                        print(f"✓ No access to {service} (expected based on roles)")
            
            print("\n✓ JWT token management test completed!")
            
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running refactored CIELO authentication tests...")
    print("Compare this with the original test_cielo_auth_flow.py to see the improvements!")
    
    test_cielo_complete_auth_flow_refactored()
    test_cielo_access_control_refactored()
    test_concurrent_cielo_sessions_refactored()
    test_jwt_token_management_refactored()
    
    print("\n✓ All refactored tests completed!")
    print("\nKey improvements:")
    print("- No manual login/logout code")
    print("- Automatic cleanup on test failure")
    print("- Consistent error handling")
    print("- Cleaner, more readable tests")
    print("- JWT token extraction built-in")