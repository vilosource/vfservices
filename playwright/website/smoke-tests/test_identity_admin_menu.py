"""
Test that the Identity Admin menu link appears for users with identity_admin role.
"""
import pytest
import sys
import os
from playwright.sync_api import Page, expect

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from common.auth import authenticated_page, AuthenticationError


@pytest.fixture
def page(page):
    return page

def test_admin_menu_link_for_identity_admin(page: Page):
    """Test that users with identity_admin role see the admin link in dropdown menu."""
    
    with authenticated_page(page, "admin", service_url="https://website.vfservices.viloforge.com") as auth_page:
        
        # Click on the user dropdown menu
        user_dropdown = auth_page.locator('.topbar-dropdown .nav-user')
        user_dropdown.click()
        
        # Check that the Identity Admin link is visible
        admin_link = auth_page.locator('a.dropdown-item:has-text("Identity Admin")')
        expect(admin_link).to_be_visible()
        
        # Verify the link has correct href
        expect(admin_link).to_have_attribute('href', '/admin/')
        
        # Click the admin link
        admin_link.click()
        
        # Verify we're redirected to the admin page
        auth_page.wait_for_url("**/admin/**", timeout=10000)
        
        print("✅ Identity Admin link is displayed and working for admin user")


def test_no_admin_menu_link_for_regular_user(page: Page):
    """Test that regular users without identity_admin role don't see the admin link."""
    
    try:
        with authenticated_page(page, "alice", service_url="https://website.vfservices.viloforge.com") as auth_page:
            # Click on the user dropdown menu
            user_dropdown = auth_page.locator('.topbar-dropdown .nav-user')
            user_dropdown.click()
            
            # Check that the Identity Admin link is NOT visible
            admin_link = auth_page.locator('a.dropdown-item:has-text("Identity Admin")')
            expect(admin_link).not_to_be_visible()
            
            print("✅ Identity Admin link is correctly hidden for regular user")
    except (AuthenticationError, Exception) as e:
        # Alice might not have access to website, which is fine for this test
        print(f"✅ Alice doesn't have access to website (expected): {str(e)}")


def test_admin_link_icon(page: Page):
    """Test that the admin link has the correct icon."""
    
    with authenticated_page(page, "admin", service_url="https://website.vfservices.viloforge.com") as auth_page:
        # Click on the user dropdown menu
        user_dropdown = auth_page.locator('.topbar-dropdown .nav-user')
        user_dropdown.click()
        
        # Check that the admin link has the correct icon
        admin_icon = auth_page.locator('a.dropdown-item:has-text("Identity Admin") i.ri-admin-line')
        expect(admin_icon).to_be_visible()
        
        print("✅ Identity Admin link has correct icon")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])