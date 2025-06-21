"""
Debug test to check if the admin link is being rendered.
"""
import pytest
from playwright.sync_api import Page


def test_debug_admin_menu(page: Page):
    """Debug test to see what's in the dropdown menu."""
    
    # Login as admin user
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    
    # Wait for successful login
    page.wait_for_function("!window.location.href.includes('/accounts/login')", timeout=10000)
    
    # Take a screenshot of the page
    page.screenshot(path="admin_logged_in.png")
    
    # Click on the user dropdown menu
    user_dropdown = page.locator('.topbar-dropdown .nav-user')
    user_dropdown.click()
    
    # Wait a bit for dropdown to open
    page.wait_for_timeout(1000)
    
    # Take a screenshot of the dropdown
    page.screenshot(path="admin_dropdown_open.png")
    
    # Get all dropdown items
    dropdown_items = page.locator('.dropdown-menu.profile-dropdown .dropdown-item').all()
    
    print(f"\nFound {len(dropdown_items)} dropdown items:")
    for i, item in enumerate(dropdown_items):
        text = item.text_content()
        href = item.get_attribute('href')
        print(f"  {i+1}. Text: '{text}', Href: '{href}'")
    
    # Check specifically for admin-related text
    admin_texts = ['Admin', 'Identity', 'admin', 'identity']
    for text in admin_texts:
        elements = page.locator(f'.dropdown-menu.profile-dropdown:has-text("{text}")').all()
        if elements:
            print(f"\nFound elements containing '{text}':")
            for elem in elements:
                print(f"  - {elem.text_content()}")
    
    # Get the HTML of the dropdown menu
    dropdown_html = page.locator('.dropdown-menu.profile-dropdown').inner_html()
    print(f"\nDropdown HTML:\n{dropdown_html[:500]}...")  # First 500 chars


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])