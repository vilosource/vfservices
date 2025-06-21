#!/usr/bin/env python3
"""Test Identity Admin Dashboard functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_identity_admin_dashboard():
    """Test that the Identity Admin dashboard loads with proper styling"""
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode for debugging
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Test login and dashboard access
        print("1. Navigating to Identity Provider login...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        
        # Login
        print("2. Logging in as alice...")
        page.fill("input[name='username']", "alice")
        page.fill("input[name='password']", "password123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Identity Admin
        print("3. Navigating to Identity Admin...")
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Take screenshot
        page.screenshot(path="identity_admin_dashboard_styled.png", full_page=True)
        print("Screenshot saved: identity_admin_dashboard_styled.png")
        
        # Check if CSS is loaded
        print("4. Checking if CSS is properly loaded...")
        
        # Check for Bootstrap styles
        bootstrap_loaded = page.evaluate("""
            () => {
                const link = document.querySelector('link[href*="bootstrap.min.css"]');
                if (link) {
                    const sheet = link.sheet || link.styleSheet;
                    return sheet && sheet.cssRules && sheet.cssRules.length > 0;
                }
                return false;
            }
        """)
        
        if bootstrap_loaded:
            print("✓ Bootstrap CSS loaded successfully")
        else:
            print("✗ Bootstrap CSS not loaded")
        
        # Check for app styles
        app_css_loaded = page.evaluate("""
            () => {
                const link = document.querySelector('link[href*="app.min.css"]');
                if (link) {
                    const sheet = link.sheet || link.styleSheet;
                    return sheet && sheet.cssRules && sheet.cssRules.length > 0;
                }
                return false;
            }
        """)
        
        if app_css_loaded:
            print("✓ App CSS loaded successfully")
        else:
            print("✗ App CSS not loaded")
        
        # Check if navbar has background color
        navbar_styled = page.evaluate("""
            () => {
                const navbar = document.querySelector('.navbar-custom');
                if (navbar) {
                    const styles = window.getComputedStyle(navbar);
                    return styles.backgroundColor !== 'rgba(0, 0, 0, 0)' && 
                           styles.backgroundColor !== 'transparent';
                }
                return false;
            }
        """)
        
        if navbar_styled:
            print("✓ Navbar styled properly")
        else:
            print("✗ Navbar not styled")
        
        # Check sidebar styling
        sidebar_styled = page.evaluate("""
            () => {
                const sidebar = document.querySelector('.left-side-menu');
                if (sidebar) {
                    const styles = window.getComputedStyle(sidebar);
                    return styles.backgroundColor !== 'rgba(0, 0, 0, 0)' && 
                           styles.backgroundColor !== 'transparent';
                }
                return false;
            }
        """)
        
        if sidebar_styled:
            print("✓ Sidebar styled properly")
        else:
            print("✗ Sidebar not styled")
        
        # Wait a bit to see the result
        time.sleep(2)
        
        browser.close()
        
        # Return success if all styles loaded
        return bootstrap_loaded and app_css_loaded and navbar_styled and sidebar_styled

if __name__ == "__main__":
    success = test_identity_admin_dashboard()
    print(f"\nTest {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)