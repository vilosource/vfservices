#!/usr/bin/env python3
"""Debug user detail view"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright

def test_user_detail_debug():
    """Debug user detail view rendering"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Login as admin
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate directly to alice's detail page (user ID 8)
        print("Navigating to alice's detail page...")
        response = page.goto("https://website.vfservices.viloforge.com/admin/users/8/")
        print(f"Response status: {response.status}")
        page.wait_for_load_state("networkidle")
        
        # Get page content
        content = page.content()
        with open('user_detail_debug.html', 'w') as f:
            f.write(content)
        print("Saved HTML to user_detail_debug.html")
        
        # Check for error messages
        error_elem = page.query_selector(".alert-danger")
        if error_elem:
            print(f"Error found: {error_elem.inner_text()}")
        
        # Check page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Check if we got redirected
        print(f"Current URL: {page.url}")
        
        browser.close()

if __name__ == "__main__":
    test_user_detail_debug()