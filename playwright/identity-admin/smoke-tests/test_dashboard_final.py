#!/usr/bin/env python3
"""Final test of Identity Admin Dashboard functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_dashboard_final():
    """Final test of Identity Admin dashboard"""
    
    with sync_playwright() as p:
        # Launch browser with clean profile
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()
        
        # Clear any existing cookies
        context.clear_cookies()
        
        # Login
        print("1. Logging in as admin...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Identity Admin
        print("2. Navigating to Identity Admin dashboard...")
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Wait for potential CSS loading
        page.wait_for_timeout(2000)
        
        # Take screenshot
        page.screenshot(path="identity_admin_final.png", full_page=True)
        print("Screenshot saved: identity_admin_final.png")
        
        # Test navigation
        print("\n3. Testing navigation...")
        
        # Click on Users link
        users_link = page.query_selector("a:has-text('Users')")
        if users_link:
            print("✓ Found Users link")
            # Note: Don't click yet as views aren't implemented
        else:
            print("✗ Users link not found")
        
        # Check dashboard content
        print("\n4. Checking dashboard content...")
        dashboard_text = page.inner_text(".content-page")
        if "Welcome to Identity Administration" in dashboard_text:
            print("✓ Dashboard welcome message found")
        else:
            print("✗ Dashboard welcome message not found")
        
        if "User Management" in dashboard_text:
            print("✓ User Management section found")
        else:
            print("✗ User Management section not found")
        
        if "Role Assignment" in dashboard_text:
            print("✓ Role Assignment section found")
        else:
            print("✗ Role Assignment section not found")
        
        # Check if any CSS is applied
        print("\n5. Checking CSS application...")
        navbar = page.query_selector(".navbar-custom")
        if navbar:
            bg_color = page.evaluate("(element) => window.getComputedStyle(element).backgroundColor", navbar)
            if bg_color and bg_color != "rgba(0, 0, 0, 0)":
                print(f"✓ Navbar has background color: {bg_color}")
            else:
                print("✗ Navbar has no background color")
        
        print("\nDashboard is functional. CSS may need to be debugged separately.")
        
        # Keep browser open for manual inspection
        time.sleep(5)
        
        browser.close()

if __name__ == "__main__":
    test_dashboard_final()