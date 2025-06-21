"""
Example of how to refactor existing tests to use the authentication utility.
This demonstrates the before and after for migration.
"""
import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
from playwright.common.auth import authenticated_page, AuthenticationError


def test_identity_admin_with_auth_utility():
    """
    Refactored version of identity admin test using the authentication utility.
    Compare this with the original test_identity_admin_comprehensive.py
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            # Use the authentication utility - much cleaner!
            with authenticated_page(page, "admin") as auth_page:
                print("✓ Successfully logged in as admin")
                
                # Test 1: Access Identity Admin
                auth_page.goto("https://website.vfservices.viloforge.com/admin/")
                assert "Identity Administration" in auth_page.title()
                print("✓ Can access Identity Admin dashboard")
                
                # Test 2: Navigate to Users
                auth_page.goto("https://website.vfservices.viloforge.com/admin/users/")
                assert "User Management" in auth_page.title()
                print("✓ Can access User Management page")
                
                # Test 3: Check JWT token
                token = auth_page.get_jwt_token()
                assert token is not None
                print(f"✓ JWT token present: {token[:20]}...")
                
                # Test 4: Navigate to specific user
                auth_page.goto("https://website.vfservices.viloforge.com/admin/users/8/")
                assert "alice" in auth_page.title()
                print("✓ Can access user detail page")
                
            # Automatic logout happens here
            print("✓ Successfully logged out")
            
        except AuthenticationError as e:
            print(f"✗ Authentication failed: {e}")
            raise
        finally:
            browser.close()


def test_multiple_users_sequential():
    """
    Example of testing with multiple users sequentially
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Test as admin
            print("\n--- Testing as admin ---")
            with authenticated_page(page, "admin") as auth_page:
                auth_page.goto("https://website.vfservices.viloforge.com/admin/")
                assert "Identity Administration" in auth_page.title()
                print("✓ Admin can access Identity Admin")
            
            # Test as alice
            print("\n--- Testing as alice ---")
            with authenticated_page(page, "alice", service_url="https://cielo.viloforge.com") as auth_page:
                # Already navigated to CIELO after login
                assert "cielo.viloforge.com" in auth_page.url
                print("✓ Alice can access CIELO")
                
                # Try to access admin (should fail)
                auth_page.goto("https://website.vfservices.viloforge.com/admin/")
                if "/login" in auth_page.url or "Access Denied" in auth_page.content():
                    print("✓ Alice correctly denied admin access")
                else:
                    print("✗ Alice should not have admin access")
            
        finally:
            browser.close()


def test_concurrent_sessions():
    """
    Example of testing with multiple browser contexts (like different browsers)
    """
    with sync_playwright() as p:
        # Create two separate browsers
        browser1 = p.chromium.launch(headless=True)
        browser2 = p.chromium.launch(headless=True)
        
        try:
            # Create contexts
            context1 = browser1.new_context(ignore_https_errors=True)
            context2 = browser2.new_context(ignore_https_errors=True)
            
            page1 = context1.new_page()
            page2 = context2.new_page()
            
            # Login both users
            with authenticated_page(page1, "admin") as admin_page:
                with authenticated_page(page2, "alice") as alice_page:
                    print("✓ Both users logged in concurrently")
                    
                    # Admin accesses admin panel
                    admin_page.goto("https://website.vfservices.viloforge.com/admin/")
                    assert "Identity Administration" in admin_page.title()
                    print("✓ Admin accessing admin panel")
                    
                    # Alice accesses CIELO
                    alice_page.goto("https://cielo.viloforge.com/")
                    assert "cielo.viloforge.com" in alice_page.url
                    print("✓ Alice accessing CIELO")
                    
                # Alice automatically logged out here
                print("✓ Alice logged out")
            # Admin automatically logged out here
            print("✓ Admin logged out")
            
        finally:
            browser1.close()
            browser2.close()


def test_error_handling():
    """
    Example of handling authentication errors
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Test with invalid credentials
            print("\n--- Testing invalid credentials ---")
            try:
                with authenticated_page(page, "invalid_user", "wrong_password") as auth_page:
                    print("✗ Should not reach here")
            except AuthenticationError as e:
                print(f"✓ Correctly caught auth error: {e}")
            
            # Test with valid user but no access to service
            print("\n--- Testing access denied ---")
            try:
                # Assuming 'bob' exists but has no CIELO access
                with authenticated_page(page, "bob", service_url="https://cielo.viloforge.com") as auth_page:
                    print("✗ Should not reach here if bob has no access")
            except AuthenticationError as e:
                if "does not have access" in str(e):
                    print(f"✓ Correctly denied access: {e}")
                else:
                    print(f"✗ Unexpected error: {e}")
            
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running refactored tests with authentication utility...\n")
    
    test_identity_admin_with_auth_utility()
    print("\n" + "="*60 + "\n")
    
    test_multiple_users_sequential()
    print("\n" + "="*60 + "\n")
    
    test_concurrent_sessions()
    print("\n" + "="*60 + "\n")
    
    test_error_handling()
    print("\n✓ All example tests completed!")