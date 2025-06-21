#!/usr/bin/env python3
"""Test Alice's access to Identity Admin after role assignment"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

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
        
        # Login as alice
        print("1. Logging in as alice...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "alice")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Check if logged in successfully
        if "login" not in page.url:
            print("✓ Logged in successfully")
        else:
            print("✗ Login failed")
            browser.close()
            return False
        
        # Navigate to Identity Admin
        print("\n2. Navigating to Identity Admin...")
        response = page.goto("https://website.vfservices.viloforge.com/admin/")
        print(f"Response status: {response.status}")
        page.wait_for_load_state("networkidle")
        
        # Check if we can access the dashboard
        if response.status == 200:
            print("✓ Successfully accessed Identity Admin dashboard")
            
            # Take screenshot
            page.screenshot(path="alice_identity_admin_access.png", full_page=True)
            print("Screenshot saved: alice_identity_admin_access.png")
            
            # Check page title
            title = page.title()
            print(f"Page title: {title}")
            
            # Check for dashboard content
            if "Identity Administration" in title:
                print("✓ Dashboard loaded correctly")
            else:
                print("✗ Dashboard title incorrect")
            
            # Check for alice's username in the navbar
            if page.query_selector("span:has-text('alice')"):
                print("✓ Alice's username shown in navbar")
            else:
                print("✗ Alice's username not found in navbar")
                
        elif response.status == 403:
            print("✗ Access denied (403 Forbidden)")
            print("Alice needs to log out and log back in to refresh her JWT token with the new role")
            
            # Get error message
            error_text = page.inner_text("body")
            print(f"Error message: {error_text}")
        else:
            print(f"✗ Unexpected status code: {response.status}")
        
        time.sleep(3)
        browser.close()
        
        return response.status == 200

if __name__ == "__main__":
    success = test_alice_identity_admin_access()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Make sure Alice has logged out from any existing sessions")
        print("2. Clear browser cookies/cache")
        print("3. Log in fresh to get a new JWT token with the identity_admin role")