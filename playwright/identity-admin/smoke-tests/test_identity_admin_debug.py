#!/usr/bin/env python3
"""Debug Identity Admin Dashboard loading issues"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

def test_identity_admin_debug():
    """Debug why Identity Admin dashboard isn't loading"""
    
    with sync_playwright() as p:
        # Launch browser in non-headless mode for debugging
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Console {msg.type}: {msg.text}"))
        page.on("pageerror", lambda msg: print(f"Page error: {msg}"))
        
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
        
        # Check if we have JWT token
        cookies = page.context.cookies()
        jwt_cookie = next((c for c in cookies if c['name'] == 'jwt_token'), None)
        if jwt_cookie:
            print(f"✓ JWT token present: {jwt_cookie['value'][:50]}...")
        else:
            print("✗ No JWT token found")
        
        # Navigate to Identity Admin
        print("\n3. Navigating to Identity Admin...")
        response = page.goto("https://website.vfservices.viloforge.com/admin/")
        print(f"Response status: {response.status}")
        print(f"Response URL: {response.url}")
        
        # Wait for content
        page.wait_for_load_state("networkidle")
        
        # Check page content
        content = page.content()
        print(f"\nPage content length: {len(content)} chars")
        
        # Check for specific elements
        title = page.title()
        print(f"Page title: {title}")
        
        # Check if there's a redirect
        if "login" in page.url.lower():
            print("⚠️  Redirected to login page")
        
        # Check for error messages
        error_elements = page.query_selector_all('.alert-danger, .error')
        if error_elements:
            print("\nError messages found:")
            for elem in error_elements:
                print(f"  - {elem.inner_text()}")
        
        # Check page HTML structure
        body_content = page.query_selector('body')
        if body_content:
            inner_html = body_content.inner_html()[:500]
            print(f"\nBody content preview:\n{inner_html}")
        
        # Take screenshot
        page.screenshot(path="identity_admin_debug.png", full_page=True)
        print("\nScreenshot saved: identity_admin_debug.png")
        
        # Check network errors
        print("\n4. Checking for failed network requests...")
        
        # Wait a bit to catch any async errors
        time.sleep(3)
        
        browser.close()

if __name__ == "__main__":
    test_identity_admin_debug()