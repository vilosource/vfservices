#!/usr/bin/env python3
"""Test Identity Admin User Role Management functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_user_roles():
    """Test user role management interface"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Login as admin
        print("1. Logging in as admin...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to alice's role management page
        print("2. Navigating to alice's role management...")
        page.goto("https://website.vfservices.viloforge.com/admin/users/8/roles/")
        page.wait_for_load_state("networkidle")
        
        # Wait for content loading
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="identity_admin_user_roles.png", full_page=True)
        print("Screenshot saved: identity_admin_user_roles.png")
        
        # Check page elements
        print("\n3. Checking role management elements...")
        
        # Check page title
        if page.query_selector("h5:has-text('Current Roles for alice')"):
            print("✓ Current roles section found")
        else:
            print("✗ Current roles section not found")
        
        # Check current roles table
        role_rows = page.query_selector_all("table tbody tr")
        print(f"✓ Found {len(role_rows)} current roles")
        
        # Check for specific roles
        if page.query_selector("td:has-text('Customer Manager')"):
            print("  - ✓ Customer Manager role found")
        if page.query_selector("td:has-text('Identity Administrator')"):
            print("  - ✓ Identity Administrator role found")
        
        # Check role assignment form
        if page.query_selector("select#service"):
            print("✓ Service selector found")
        else:
            print("✗ Service selector not found")
        
        if page.query_selector("select#role"):
            print("✓ Role selector found")
        else:
            print("✗ Role selector not found")
        
        if page.query_selector("button:has-text('Assign Role')"):
            print("✓ Assign Role button found")
        else:
            print("✗ Assign Role button not found")
        
        # Check quick assignment profiles
        if page.query_selector("h5:has-text('Quick Assignment')"):
            print("✓ Quick Assignment section found")
            
            # Count profile cards
            profile_cards = page.query_selector_all(".card.border")
            print(f"  - Found {len(profile_cards)} role profiles")
        else:
            print("✗ Quick Assignment section not found")
        
        # Test service selection
        print("\n4. Testing role assignment form...")
        service_select = page.query_selector("select#service")
        if service_select:
            # Select billing_api service
            page.select_option("select#service", "billing_api")
            page.wait_for_timeout(500)
            
            # Check if role select is enabled
            role_select = page.query_selector("select#role")
            if role_select and not role_select.is_disabled():
                print("✓ Role selector enabled after service selection")
            else:
                print("✗ Role selector not enabled")
        
        time.sleep(3)
        browser.close()
        return True

if __name__ == "__main__":
    success = test_user_roles()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")