import pytest
from playwright.sync_api import Page, expect
import os

BASE_URL = "https://cielo.viloforge.com"
IDENTITY_ADMIN_USER = os.getenv("IDENTITY_ADMIN_USER", "admin")
IDENTITY_ADMIN_PASSWORD = os.getenv("IDENTITY_ADMIN_PASSWORD", "admin123")

@pytest.fixture(autouse=True)
def login_as_identity_admin(page: Page):
    """Login as identity admin user before each test"""
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill("#username", IDENTITY_ADMIN_USER)
    page.fill("#password", IDENTITY_ADMIN_PASSWORD)
    page.click("button[type='submit']")
    
    # Wait for successful login - could redirect to different URLs
    page.wait_for_load_state("networkidle")
    
    # Verify we're logged in by checking for the user dropdown
    assert page.locator("button#topnav-headerDropdown").is_visible()
    yield

def test_identity_admin_link_in_dropdown(page: Page):
    """Test that Identity Admin link appears in dropdown for users with identity_admin role"""
    # Click on user dropdown
    page.click("button#topnav-headerDropdown")
    
    # Wait for dropdown to be visible
    dropdown = page.locator(".dropdown-menu[aria-labelledby='topnav-headerDropdown']")
    expect(dropdown).to_be_visible()
    
    # Check that Identity Admin link is present
    identity_admin_link = page.locator("a.dropdown-item:has-text('Identity Admin')")
    expect(identity_admin_link).to_be_visible()
    
    # Verify the link has correct href
    expect(identity_admin_link).to_have_attribute("href", "https://identity.vfservices.viloforge.com/admin/")
    
    # Verify the icon is present
    icon = identity_admin_link.locator("i.ri-admin-line")
    expect(icon).to_be_visible()

def test_identity_admin_link_navigation(page: Page):
    """Test that clicking Identity Admin link navigates to correct URL"""
    # Click on user dropdown
    page.click("button#topnav-headerDropdown")
    
    # Click on Identity Admin link
    with page.expect_navigation():
        page.click("a.dropdown-item:has-text('Identity Admin')")
    
    # Verify we navigated to the identity admin URL
    expect(page).to_have_url("https://identity.vfservices.viloforge.com/admin/")