"""
Test CIELO Admin dropdown menu item functionality.
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://cielo.viloforge.com"
IDENTITY_ADMIN_URL = "https://identity.cielo.viloforge.com/admin/"

def test_cielo_admin_menu_item_visible_with_role(page: Page):
    """Test that CIELO Admin menu item is visible for users with cielo_admin role."""
    # Login as admin user who has cielo_admin role
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123!#QWERT')
    page.click('button[type="submit"]')
    
    # Wait for login to complete
    page.wait_for_url(BASE_URL + "/", timeout=10000)
    
    # Click on user dropdown
    page.locator('.topbar-dropdown .nav-user').click()
    
    # Wait for dropdown to be visible
    page.wait_for_selector('.dropdown-menu.profile-dropdown', state='visible')
    
    # Check that CIELO Admin menu item is visible
    admin_item = page.locator('a.dropdown-item:has-text("CIELO Admin")')
    expect(admin_item).to_be_visible()
    
    # Check the href
    href = admin_item.get_attribute('href')
    assert href == IDENTITY_ADMIN_URL, f"Expected href to be {IDENTITY_ADMIN_URL}, got {href}"


def test_cielo_admin_menu_item_hidden_without_role(page: Page):
    """Test that CIELO Admin menu item is not visible for users without cielo_admin role."""
    # We need a user who has CIELO access but not cielo_admin role
    # Since alice doesn't have CIELO access at all, this test needs a different approach
    # For now, we'll skip this test as we don't have a suitable test user
    pytest.skip("Need a user with CIELO access but without cielo_admin role")


def test_cielo_admin_menu_link_functionality(page: Page):
    """Test that clicking CIELO Admin menu item redirects to identity admin."""
    # Login as admin user
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123!#QWERT')
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
    
    # Should redirect to identity admin URL
    # Wait a bit for the navigation to start
    page.wait_for_timeout(2000)
    
    # Verify we're on the identity admin page (or login page if not authenticated there)
    assert IDENTITY_ADMIN_URL in page.url or "identity.cielo.viloforge.com" in page.url, f"Expected to be on identity admin domain, but on {page.url}"