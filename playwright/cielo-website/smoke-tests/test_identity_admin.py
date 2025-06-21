"""
Test Identity Admin functionality with real API integration
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://website.vfservices.viloforge.com"


def test_identity_admin_real_api(page: Page):
    """Test that the Identity Admin interface works with the real API."""
    
    # Go to login page
    page.goto(f"{BASE_URL}/login/")
    page.wait_for_load_state("networkidle")
    
    # Login as alice
    page.fill("input[name='email']", "alice")
    page.fill("input[name='password']", "alicepassword")
    page.click("button[type='submit']")
    
    # Wait for login to complete
    page.wait_for_url("**/", timeout=10000)
    time.sleep(1)  # Give time for JWT to be set
    
    # Navigate to admin users page
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_load_state("networkidle")
    
    # Wait for users table to load
    page.wait_for_selector("#userTable", state="visible", timeout=10000)
    
    # Take screenshot for debugging
    page.screenshot(path="identity_admin_users_list.png")
    
    # Check that we're showing all users
    pagination_info = page.locator("#pagination-info").text_content()
    print(f"Pagination info: {pagination_info}")
    assert "18 users" in pagination_info, f"Expected to see 18 users, but got: {pagination_info}"
    
    # Verify some known users are visible
    table = page.locator("#userTable tbody")
    assert table.locator("tr").count() > 10, "Should show more than 10 users"
    
    # Check for specific users (using more specific selectors)
    assert table.locator("td:has-text('alice')").first.is_visible()
    assert table.locator("td:has-text('bob')").first.is_visible()
    assert table.locator("td:has-text('charlie')").first.is_visible()
    assert table.locator("td:has-text('david')").first.is_visible()
    
    # Test filtering
    page.fill("#searchInput", "alice")
    page.click("#applyFilters")
    time.sleep(2)  # Wait for filtering
    
    # Check filtered results
    table_rows = page.locator("#userTable tbody tr")
    filtered_count = table_rows.count()
    print(f"Filtered results count: {filtered_count}")
    assert filtered_count == 1, f"Should show only 1 user when searching for alice, but got {filtered_count}"
    
    # Clear filters
    page.click("#clearFilters")
    time.sleep(2)  # Wait for clear
    
    # Should show all users again
    pagination_info_after = page.locator("#pagination-info").text_content()
    print(f"Pagination info after clear: {pagination_info_after}")
    assert "18 users" in pagination_info_after, "Should show all users after clearing filters"
    
    print("✅ Identity Admin real API integration test passed!")


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        page = context.new_page()
        
        try:
            test_identity_admin_real_api(page)
        finally:
            browser.close()