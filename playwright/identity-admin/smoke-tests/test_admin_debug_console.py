#!/usr/bin/env python3
"""Debug Identity Admin Dashboard with console logging"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_admin_dashboard_debug():
    """Test admin dashboard with console debugging"""
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode for debugging
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        page.on("pageerror", lambda msg: print(f"Page error: {msg}"))
        page.on("response", lambda response: print(f"Response: {response.status} {response.url}") if response.status >= 400 else None)
        
        # Test login and dashboard access
        print("1. Navigating to Identity Provider login...")
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        
        # Login as admin
        print("\n2. Logging in as admin...")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        # Navigate to Identity Admin
        print("\n3. Navigating to Identity Admin...")
        response = page.goto("https://website.vfservices.viloforge.com/admin/")
        print(f"Main response: {response.status} {response.url}")
        page.wait_for_load_state("networkidle")
        
        # Get page content
        content = page.content()
        print(f"\nPage content length: {len(content)} chars")
        
        # Check body content
        body = page.query_selector("body")
        if body:
            text = body.inner_text()
            print(f"Body text preview: {text[:200]}")
        
        # Wait for any delayed errors
        time.sleep(3)
        
        browser.close()

if __name__ == "__main__":
    test_admin_dashboard_debug()