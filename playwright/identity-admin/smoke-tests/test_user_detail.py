#!/usr/bin/env python3
"""Test Identity Admin User Detail functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_user_detail():
    """Test user detail view"""
    
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
        
        # Navigate to user list
        print("2. Navigating to user list...")
        page.goto("https://website.vfservices.viloforge.com/admin/users/")
        page.wait_for_load_state("networkidle")
        
        # Click on alice's username
        print("3. Clicking on alice's username...")
        alice_link = page.query_selector("a:has-text('alice')")
        if alice_link:
            alice_link.click()
            page.wait_for_load_state("networkidle")
            print("✓ Navigated to alice's detail page")
        else:
            print("✗ Alice link not found")
            browser.close()
            return False
        
        # Wait for content loading
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="identity_admin_user_detail.png", full_page=True)
        print("Screenshot saved: identity_admin_user_detail.png")
        
        # Check page elements
        print("\n4. Checking user detail elements...")
        
        # Check user info
        if page.query_selector("h4:has-text('alice')"):
            print("✓ Username displayed")
        else:
            print("✗ Username not found")
        
        # Check email
        if page.query_selector("span:has-text('alice@example.com')"):
            print("✓ Email displayed")
        else:
            print("✗ Email not found")
        
        # Check status badge
        if page.query_selector(".badge:has-text('Active')"):
            print("✓ Active status displayed")
        else:
            print("✗ Active status not found")
        
        # Check roles section
        if page.query_selector("h5:has-text('Assigned Roles')"):
            print("✓ Roles section found")
            
            # Count roles
            role_rows = page.query_selector_all("table tbody tr")
            print(f"  - Found {len(role_rows)} assigned roles")
        else:
            print("✗ Roles section not found")
        
        # Check action buttons
        if page.query_selector("a:has-text('Edit User')"):
            print("✓ Edit User button found")
        else:
            print("✗ Edit User button not found")
        
        if page.query_selector("a:has-text('Manage Roles')"):
            print("✓ Manage Roles button found")
        else:
            print("✗ Manage Roles button not found")
        
        # Test Edit button
        print("\n5. Testing Edit User button...")
        edit_button = page.query_selector("a:has-text('Edit User')")
        if edit_button:
            edit_button.click()
            page.wait_for_load_state("networkidle")
            
            # Check if we're on the edit page
            if "edit" in page.url:
                print("✓ Navigated to edit page")
                page.screenshot(path="identity_admin_user_edit.png", full_page=True)
                print("Screenshot saved: identity_admin_user_edit.png")
                
                # Check form fields
                if page.query_selector("input#username[value='alice']"):
                    print("✓ Username field populated")
                if page.query_selector("input#email"):
                    print("✓ Email field found")
                if page.query_selector("input#first_name"):
                    print("✓ First name field found")
                if page.query_selector("input#is_active"):
                    print("✓ Active status checkbox found")
            else:
                print("✗ Failed to navigate to edit page")
        
        time.sleep(3)
        browser.close()
        return True

if __name__ == "__main__":
    success = test_user_detail()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")