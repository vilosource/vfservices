"""
Test CIELO Admin dropdown menu item functionality.
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://cielo.viloforge.com"
ADMIN_URL = f"{BASE_URL}/admin/"

def test_cielo_admin_menu_item_visible_with_role(page: Page):
    """Test that CIELO Admin menu item is visible for users with cielo_admin role."""
    # Login as cielo_admin user who should have cielo_admin role
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', 'cielo_admin')
    page.fill('input[name="password"]', 'cielo_admin123!#QWERT')
    page.click('button[type="submit"]')
    
    # Wait for login to complete - might get an error or redirect
    page.wait_for_timeout(3000)
    
    # Check where we ended up
    current_url = page.url
    print(f"Current URL after login: {current_url}")
    
    # If we're still on login page, check for errors
    if "/accounts/login" in current_url:
        error_msg = page.locator('.alert').text_content() if page.locator('.alert').count() > 0 else "No error message"
        print(f"Login error: {error_msg}")
        
    # Make sure we're on the home page
    if current_url != BASE_URL + "/":
        page.goto(BASE_URL + "/")
    
    # Click on user dropdown
    page.locator('.topbar-dropdown .nav-user').click()
    
    # Wait for dropdown to be visible
    page.wait_for_selector('.dropdown-menu.profile-dropdown', state='visible')
    
    # Check that CIELO Admin menu item is visible
    admin_item = page.locator('a.dropdown-item:has-text("CIELO Admin")')
    expect(admin_item).to_be_visible()
    
    # Check the href
    href = admin_item.get_attribute('href')
    assert href == "/admin/", f"Expected href to be /admin/, got {href}"


def test_cielo_admin_menu_item_hidden_without_role(page: Page):
    """Test that CIELO Admin menu item is not visible for users without cielo_admin role."""
    # We need a user who has CIELO access but not cielo_admin role
    # Since alice doesn't have CIELO access at all, this test needs a different approach
    # For now, we'll skip this test as we don't have a suitable test user
    pytest.skip("Need a user with CIELO access but without cielo_admin role")


def test_cielo_admin_menu_link_functionality(page: Page):
    """Test that clicking CIELO Admin menu item redirects to local identity admin."""
    # Login as cielo_admin user
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', 'cielo_admin')
    page.fill('input[name="password"]', 'cielo_admin123!#QWERT')
    page.click('button[type="submit"]')
    
    # Wait for login to complete
    page.wait_for_url(BASE_URL + "/", timeout=10000)
    
    # Click on user dropdown
    page.locator('.topbar-dropdown .nav-user').click()
    
    # Wait for dropdown to be visible
    page.wait_for_selector('.dropdown-menu.profile-dropdown', state='visible')
    
    # Click on CIELO Admin menu item
    admin_item = page.locator('a.dropdown-item:has-text("CIELO Admin")')
    admin_item.click()
    
    # Should redirect to local admin URL
    page.wait_for_url(ADMIN_URL + "*", timeout=10000)
    
    # Verify we're on the admin page
    assert page.url.startswith(ADMIN_URL), f"Expected to be on {ADMIN_URL}, but on {page.url}"
    
    # Check that the identity admin dashboard loaded
    expect(page.locator('h1:has-text("Identity Administration")')).to_be_visible(timeout=10000)