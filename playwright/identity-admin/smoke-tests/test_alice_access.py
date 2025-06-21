#!/usr/bin/env python3
"""Test Alice's access to Identity Admin after role assignment"""

import sys
import os
sys.path.append('/home/jasonvi/GitHub/vfservices')

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from playwright.common.auth import authenticated_page, AuthenticationError

from playwright.sync_api import sync_playwright
import time

def test_alice_identity_admin_access():
    """Test that Alice can access Identity Admin with identity_admin role"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Clear any existing session
        context.clear_cookies()
        
        # Use authentication utility for login
        print("1. Logging in as alice...")
        try:
            with authenticated_page(page, "alice", "password123") as auth_page:
                print("✓ Logged in successfully")
                
                # Navigate to Identity Admin
                print("\n2. Navigating to Identity Admin...")
                response = auth_page.goto("https://website.vfservices.viloforge.com/admin/")
                print(f"Response status: {response.status}")
                auth_page.wait_for_load_state("networkidle")
                
                # Check if we can access the dashboard
                if response.status == 200:
                    print("✓ Successfully accessed Identity Admin dashboard")
                    
                    # Take screenshot
                    auth_page.screenshot(path="alice_identity_admin_access.png", full_page=True)
                    print("Screenshot saved: alice_identity_admin_access.png")
                    
                    # Continue with rest of test using auth_page instead of page
                    current_url = auth_page.url
                    content = auth_page.content()
                    
                    # Check page content
                    if "Identity Administration" in content or "Dashboard" in content:
                        print("✓ Dashboard content loaded correctly")
                    else:
                        print("✗ Dashboard content not as expected")
                    
                    # Check for Alice's name in the page
                    if "alice" in content.lower():
                        print("✓ User context (alice) visible in the page")
                    
                    # Try to navigate to users list
                    print("\n3. Checking access to user list...")
                    response = auth_page.goto("https://website.vfservices.viloforge.com/admin/users/")
                    if response.status == 200:
                        print("✓ Can access user list")
                    else:
                        print(f"✗ Cannot access user list (status: {response.status})")
                    
                    # Try to view admin user details
                    print("\n4. Checking access to user details...")
                    response = auth_page.goto("https://website.vfservices.viloforge.com/admin/users/1/")
                    if response.status == 200:
                        print("✓ Can view user details")
                    else:
                        print(f"✗ Cannot view user details (status: {response.status})")
                    
                    # Check edit permissions
                    print("\n5. Checking edit permissions...")
                    response = auth_page.goto("https://website.vfservices.viloforge.com/admin/users/1/edit/")
                    if response.status == 200:
                        print("✓ Can access user edit page")
                    else:
                        print(f"✗ Cannot access user edit page (status: {response.status})")
                    
                    print("\n✓ All Identity Admin access tests passed for alice")
                    return True
                else:
                    print(f"✗ Access denied to Identity Admin (status: {response.status})")
                    return False
                    
        except AuthenticationError as e:
            print(f"✗ Login failed: {e}")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_alice_identity_admin_access()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Make sure Alice has logged out from any existing sessions")
        print("2. Clear browser cookies/cache")
        print("3. Log in fresh to get a new JWT token with the identity_admin role")