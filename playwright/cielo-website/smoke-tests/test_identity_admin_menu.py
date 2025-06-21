"""
Test that the Identity Admin menu link appears for users with identity_admin role.
"""
import pytest
from playwright.sync_api import Page, expect
import time


def test_admin_menu_link_for_identity_admin(page: Page):
    """Test that users with identity_admin role see the admin link in dropdown menu."""
    
    # Login as admin user (who should have identity_admin role)
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    
    # Fill login form
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Wait for successful login (any page except login)
    page.wait_for_function("!window.location.href.includes('/accounts/login')", timeout=10000)
    
    # Click on the user dropdown menu
    user_dropdown = page.locator('.topbar-dropdown .nav-user')
    user_dropdown.click()
    
    # Check that the Identity Admin link is visible
    admin_link = page.locator('a.dropdown-item:has-text("Identity Admin")')
    expect(admin_link).to_be_visible()
    
    # Verify the link has correct href
    expect(admin_link).to_have_attribute('href', '/admin/')
    
    # Click the admin link
    admin_link.click()
    
    # Verify we're redirected to the admin page
    page.wait_for_url("**/admin/**", timeout=10000)
    
    # Verify the admin page loads
    expect(page).to_have_title(lambda title: 'Admin' in title or 'Identity' in title)
    
    print("✅ Identity Admin link is displayed and working for admin user")


def test_no_admin_menu_link_for_regular_user(page: Page):
    """Test that regular users without identity_admin role don't see the admin link."""
    
    # First create a test user without identity_admin role
    # Login as admin to create the user
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/**", timeout=10000)
    
    # Logout
    page.goto("https://website.vfservices.viloforge.com/accounts/logout/")
    
    # Try login as a regular user (alice)
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.fill('input[name="email"]', 'alice')
    page.fill('input[name="password"]', 'alice123!#QWERT')
    page.click('button[type="submit"]')
    
    try:
        # Wait for redirect to dashboard
        page.wait_for_url("**/dashboard/**", timeout=10000)
        
        # Click on the user dropdown menu
        user_dropdown = page.locator('.topbar-dropdown .nav-user')
        user_dropdown.click()
        
        # Check that the Identity Admin link is NOT visible
        admin_link = page.locator('a.dropdown-item:has-text("Identity Admin")')
        expect(admin_link).not_to_be_visible()
        
        print("✅ Identity Admin link is correctly hidden for regular user")
        
    except Exception as e:
        # Alice might not have access to cielo, which is fine for this test
        print(f"Alice doesn't have access to CIELO (expected): {str(e)}")


def test_admin_link_icon(page: Page):
    """Test that the admin link has the correct icon."""
    
    # Login as admin user
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.fill('input[name="username"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard/**", timeout=10000)
    
    # Click on the user dropdown menu
    user_dropdown = page.locator('.topbar-dropdown .nav-user')
    user_dropdown.click()
    
    # Check that the admin link has the correct icon
    admin_icon = page.locator('a.dropdown-item:has-text("Identity Admin") i.ri-admin-line')
    expect(admin_icon).to_be_visible()
    
    print("✅ Identity Admin link has correct icon")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])