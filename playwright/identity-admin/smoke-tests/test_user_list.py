#!/usr/bin/env python3
"""Test Identity Admin User List functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_user_list():
    """Test user list view"""
    
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
        
        # Navigate to Identity Admin
        print("2. Navigating to Identity Admin...")
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Click on Users link
        print("3. Clicking on Users link...")
        users_link = page.query_selector("a:has-text('Users')")
        if users_link:
            users_link.click()
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to user list")
        else:
            print("✗ Users link not found")
            browser.close()
            return False
        
        # Wait for potential content loading
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="identity_admin_user_list.png", full_page=True)
        print("Screenshot saved: identity_admin_user_list.png")
        
        # Check page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Check for user table
        user_table = page.query_selector("#userTable")
        if user_table:
            print("✓ User table found")
            
            # Count rows
            rows = page.query_selector_all("#userTable tbody tr")
            print(f"  - Found {len(rows)} user rows")
            
            # Check for specific users
            if page.query_selector("td:has-text('admin')"):
                print("  - ✓ Admin user found")
            if page.query_selector("td:has-text('alice')"):
                print("  - ✓ Alice user found")
        else:
            print("✗ User table not found")
        
        # Check for filters
        if page.query_selector("#searchInput"):
            print("✓ Search input found")
        else:
            print("✗ Search input not found")
        
        if page.query_selector("#statusFilter"):
            print("✓ Status filter found")
        else:
            print("✗ Status filter not found")
        
        # Check for create user button
        if page.query_selector("a:has-text('Create User')"):
            print("✓ Create User button found")
        else:
            print("✗ Create User button not found")
        
        time.sleep(3)
        browser.close()
        return True

if __name__ == "__main__":
    success = test_user_list()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")