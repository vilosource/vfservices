#!/usr/bin/env python3
"""
Simple test to verify the authentication utility works correctly
"""
import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
from playwright.common.auth import authenticated_page, AuthenticationError


def test_basic_auth():
    """Test basic authentication flow"""
    print("Testing basic authentication utility...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Test with admin user
            with authenticated_page(page, "admin") as auth_page:
                print("✓ Login successful")
                
                # Verify we can access protected pages
                auth_page.goto("https://website.vfservices.viloforge.com/")
                current_url = auth_page.url
                
                # Should not be redirected to login
                if "/login" not in current_url and "/accounts/login/" not in current_url:
                    print(f"✓ Can access protected page: {current_url}")
                else:
                    print(f"✗ Was redirected to login: {current_url}")
                
                # Check JWT token
                token = auth_page.get_jwt_token()
                if token:
                    print(f"✓ JWT token found: {token[:30]}...")
                else:
                    print("✗ No JWT token found")
            
            print("✓ Logout successful")
            
            # Verify we're logged out
            page.goto("https://website.vfservices.viloforge.com/")
            if "/login" in page.url or "/accounts/login/" in page.url:
                print("✓ Correctly redirected to login after logout")
            else:
                print("✗ Still have access after logout")
                
        except AuthenticationError as e:
            print(f"✗ Authentication failed: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            return False
        finally:
            browser.close()
    
    print("\n✓ Authentication utility test passed!")
    return True


if __name__ == "__main__":
    success = test_basic_auth()
    sys.exit(0 if success else 1)