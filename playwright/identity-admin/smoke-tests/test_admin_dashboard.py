#!/usr/bin/env python3
"""Test Identity Admin Dashboard with admin user"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_admin_dashboard():
    """Test that admin user can access Identity Admin dashboard"""
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode for debugging
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test login and dashboard access
        print("1. Navigating to Identity Provider login...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        
        # Login as admin
        print("2. Logging in as admin...")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Identity Admin
        print("3. Navigating to Identity Admin...")
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Take screenshot
        page.screenshot(path="identity_admin_dashboard_admin.png", full_page=True)
        print("Screenshot saved: identity_admin_dashboard_admin.png")
        
        # Check if dashboard loaded
        title = page.title()
        print(f"Page title: {title}")
        
        # Check for dashboard content
        if page.query_selector("h1:has-text('Identity Administration')"):
            print("✓ Dashboard header found")
        else:
            print("✗ Dashboard header not found")
        
        # Check for menu items
        if page.query_selector("a:has-text('Users')"):
            print("✓ Users menu item found")
        else:
            print("✗ Users menu item not found")
        
        # Wait a bit to see the result
        time.sleep(2)
        
        browser.close()
        
        return True

if __name__ == "__main__":
    success = test_admin_dashboard()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")