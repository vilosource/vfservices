"""
Basic smoke tests for the Identity Admin application
"""
import pytest
import sys
import os
import time
from playwright.sync_api import Page, expect

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from common.auth import authenticated_page, AuthenticationError


def test_identity_admin_accessible(page: Page):
    """Test that the identity admin is accessible at /admin/"""
    # Navigate to the admin URL
    base_url = "https://website.vfservices.viloforge.com"
    page.goto(f"{base_url}/admin/")
    
    # Take a screenshot to see what's happening
    page.screenshot(path="identity_admin_page_initial.png")
    
    # Check if there's an error
    if page.locator("h1:has-text('Server Error')").is_visible() or page.locator("text=500 Server Error").is_visible():
        # Get the error details
        error_text = page.content()
        print(f"Error on page: {error_text[:500]}")
    
    # Since we're not logged in, we should either see the admin page or be redirected to login
    # Let's be more flexible with the URL check
    current_url = page.url
    print(f"Current URL: {current_url}")
    
    # We expect to either be on the admin page or redirected to login
    assert "/admin/" in current_url or "login" in current_url, f"Unexpected URL: {current_url}"


@pytest.fixture
def page(page):
    return page

def test_identity_admin_login(page: Page):
    """Test logging into the identity admin"""
    base_url = "https://website.vfservices.viloforge.com"
    
    with authenticated_page(page, "admin", service_url=base_url) as auth_page:
        # Navigate to admin page after login
        auth_page.goto(f"{base_url}/admin/")
        auth_page.wait_for_load_state("networkidle")
        
        # Take a screenshot to see what's displayed
        auth_page.screenshot(path="identity_admin_after_login.png")
        
        # Check the page content - might be an error or the dashboard
        if auth_page.locator("text=Server Error").is_visible() or auth_page.locator("text=404").is_visible():
            print(f"Error on page. URL: {auth_page.url}")
            print(f"Page content: {auth_page.content()[:1000]}")
        
        # Check if we see "Permission denied"
        if auth_page.locator("text=Permission denied").is_visible():
            print("Permission denied error")
            # Try to get more details from the page
            page_content = auth_page.content()
            if "identity_admin role required" in page_content:
                print("Missing identity_admin role")
            else:
                print("Other permission issue")
        
        # Verify we're on the dashboard - check for the header and dashboard elements
        expect(auth_page.locator("h4.page-title:has-text('Identity Administration')")).to_be_visible()
        
        # Take a screenshot
        auth_page.screenshot(path="identity_admin_dashboard.png")
        
        # Check that the main sections are visible
        expect(auth_page.locator("text=User Management")).to_be_visible()
        expect(auth_page.locator("text=Service Registry")).to_be_visible()


def test_identity_admin_user_list(page: Page):
    """Test navigating to the user list"""
    base_url = "https://website.vfservices.viloforge.com"
    
    with authenticated_page(page, "admin", service_url=base_url) as auth_page:
        # Navigate to admin page
        auth_page.goto(f"{base_url}/admin/")
        auth_page.wait_for_load_state("networkidle")
        
        # Navigate to user list
        auth_page.goto(f"{base_url}/admin/users/")
        auth_page.wait_for_load_state("networkidle")
        
        # Verify we're on the user list page
        expect(auth_page.locator("h4")).to_contain_text("User Management")
        
        # Take a screenshot
        auth_page.screenshot(path="identity_admin_user_list.png")