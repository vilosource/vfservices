import pytest
from playwright.sync_api import Page, expect

# Test URLs
BASE_URL = "https://cielo.viloforge.com"

def test_user_without_cielo_roles_sees_error_page(page: Page):
    """Test that users without CIELO roles are redirected to access error page after login."""
    # Clear any existing cookies
    page.context.clear_cookies()
    
    # Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    
    # Login with user that has no CIELO roles
    page.fill('input[name="email"]', 'testuser')
    page.fill('input[name="password"]', 'testuser123')
    page.click('button[type="submit"]')
    
    # Should be redirected to access error page
    page.wait_for_url(f"{BASE_URL}/accounts/access-error/")
    expect(page).to_have_url(f"{BASE_URL}/accounts/access-error/")
    
    # Verify error page content
    expect(page.locator('h2')).to_contain_text('Access Denied')
    expect(page.locator('.alert-danger')).to_contain_text('Insufficient Access Rights')
    
    # Verify required roles are shown
    expect(page.locator('body')).to_contain_text('cielo_admin')
    expect(page.locator('body')).to_contain_text('cielo_user')
    expect(page.locator('body')).to_contain_text('cloud_architect')
    expect(page.locator('body')).to_contain_text('cost_analyst')
    
    # Verify action buttons
    expect(page.locator('a:has-text("Go to VF Services Home")')).to_be_visible()
    expect(page.locator('a:has-text("Logout")')).to_be_visible()

def test_user_with_cielo_role_bypasses_error_page(page: Page):
    """Test that users with CIELO roles do not see the error page."""
    # Clear any existing cookies
    page.context.clear_cookies()
    
    # Navigate to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    
    # Login with user that has CIELO roles (alice has cielo_user role)
    page.fill('input[name="email"]', 'alice')
    page.fill('input[name="password"]', 'password123')
    page.click('button[type="submit"]')
    
    # Should NOT be on error page
    page.wait_for_url(f"{BASE_URL}/")
    expect(page).to_have_url(f"{BASE_URL}/")
    expect(page).not_to_have_url(f"{BASE_URL}/accounts/access-error/")

def test_direct_access_to_error_page(page: Page):
    """Test that the error page can be accessed directly."""
    # Clear cookies
    page.context.clear_cookies()
    
    # Go directly to error page
    page.goto(f"{BASE_URL}/accounts/access-error/")
    
    # Should load successfully
    expect(page).to_have_url(f"{BASE_URL}/accounts/access-error/")
    expect(page.locator('h2')).to_contain_text('Access Denied')
    
    # Should show message for anonymous users
    expect(page.locator('body')).to_contain_text('You currently have no roles')

def test_error_page_shows_user_info_when_authenticated(page: Page):
    """Test that error page shows user info when accessed by authenticated user."""
    # Clear cookies and login first
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', 'testuser')
    page.fill('input[name="password"]', 'testuser123')
    page.click('button[type="submit"]')
    
    # Should be on error page
    page.wait_for_url(f"{BASE_URL}/accounts/access-error/")
    
    # Should show logged in user info
    expect(page.locator('footer')).to_contain_text('Logged in as: testuser')