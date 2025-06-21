#!/usr/bin/env python3
"""Test Identity Admin Dashboard HTML content"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright

def test_dashboard_html():
    """Test dashboard HTML content"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Login
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Identity Admin
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Get page HTML
        html = page.content()
        
        # Save to file
        with open('identity_admin_dashboard.html', 'w') as f:
            f.write(html)
        print("Saved dashboard HTML to identity_admin_dashboard.html")
        
        # Check for key elements
        elements = {
            'sidebar': page.query_selector('.left-side-menu'),
            'navbar': page.query_selector('.navbar-custom'),
            'content': page.query_selector('.content-page'),
            'users_link': page.query_selector("a[href*='user_list']"),
            'roles_link': page.query_selector("a[href*='role_list']"),
        }
        
        for name, elem in elements.items():
            if elem:
                print(f"✓ {name} found")
            else:
                print(f"✗ {name} not found")
        
        browser.close()

if __name__ == "__main__":
    test_dashboard_html()