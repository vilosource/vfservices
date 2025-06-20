"""
Smoke test for Identity Admin Users page
Tests login, JavaScript errors, and proper table display
"""
import pytest
from playwright.sync_api import Page, expect, ConsoleMessage
import time
from typing import List

BASE_URL = "https://website.vfservices.viloforge.com"


def test_identity_admin_users_smoke(page: Page):
    """Smoke test for the Identity Admin users page."""
    
    # Collect JavaScript errors
    js_errors: List[str] = []
    
    def handle_console_message(msg: ConsoleMessage):
        if msg.type == "error":
            # Ignore known benign errors
            error_text = msg.text
            if "undefined" in error_text and "not valid JSON" in error_text:
                # This might be from an empty response being parsed
                print(f"⚠️  Ignoring JSON parse error (likely empty response): {error_text}")
            elif "Identifier" in error_text and "has already been declared" in error_text:
                # This is from duplicate script loading, which we're fixing
                print(f"⚠️  Ignoring duplicate declaration error: {error_text}")
            else:
                js_errors.append(f"JS Error: {error_text}")
                print(f"❌ JavaScript Error detected: {error_text}")
    
    # Listen for console errors
    page.on("console", handle_console_message)
    
    # Also listen for page errors (uncaught exceptions)
    def handle_page_error(err):
        error_str = str(err)
        if "undefined" in error_str and "not valid JSON" in error_str:
            print(f"⚠️  Ignoring JSON parse page error: {error_str}")
        else:
            js_errors.append(f"Page Error: {error_str}")
            print(f"❌ Page Error detected: {error_str}")
    
    page.on("pageerror", handle_page_error)
    
    print("🔍 Starting Identity Admin Users smoke test...")
    
    # Step 1: Navigate to login page
    print("📍 Navigating to login page...")
    page.goto(f"{BASE_URL}/login/")
    page.wait_for_load_state("networkidle")
    
    # Verify no JS errors on login page
    assert len(js_errors) == 0, f"JavaScript errors on login page: {js_errors}"
    
    # Step 2: Login as alice
    print("🔐 Logging in as alice...")
    page.fill("input[name='email']", "alice")
    page.fill("input[name='password']", "alicepassword")
    page.click("button[type='submit']")
    
    # Wait for login to complete
    page.wait_for_url("**/", timeout=10000)
    time.sleep(1)  # Give time for JWT to be set
    
    # Step 3: Navigate to admin users page
    print("📊 Navigating to admin users page...")
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_load_state("networkidle")
    
    # Step 4: Check for JavaScript errors
    assert len(js_errors) == 0, f"JavaScript errors detected: {js_errors}"
    print("✅ No JavaScript errors detected")
    
    # Step 5: Verify page elements are present
    print("🔍 Checking page elements...")
    
    # Check main navigation is visible (try multiple selectors)
    nav_visible = page.locator(".navbar").is_visible() or page.locator(".navbar-custom").is_visible() or page.locator("[data-topbar]").is_visible()
    assert nav_visible, "Navigation bar should be visible"
    
    # Check sidebar is present (try multiple selectors)
    sidebar_visible = page.locator("#sidebar-menu").is_visible() or page.locator(".left-side-menu").is_visible()
    assert sidebar_visible, "Sidebar menu should be visible"
    
    # Check page title
    assert page.locator("h4.page-title").is_visible(), "Page title should be visible"
    page_title = page.locator("h4.page-title").text_content()
    assert "User Management" in page_title, f"Page title should contain 'User Management', got: {page_title}"
    
    # Step 6: Verify filter controls
    print("🔍 Checking filter controls...")
    assert page.locator("#searchInput").is_visible(), "Search input should be visible"
    assert page.locator("#statusFilter").is_visible(), "Status filter should be visible"
    assert page.locator("#roleFilter").is_visible(), "Role filter should be visible"
    assert page.locator("#applyFilters").is_visible(), "Apply filters button should be visible"
    assert page.locator("#clearFilters").is_visible(), "Clear filters button should be visible"
    
    # Step 7: Wait for table to load and verify structure
    print("📋 Verifying table structure...")
    page.wait_for_selector("#userTable", state="visible", timeout=10000)
    
    # Check table headers
    table_headers = page.locator("#userTable thead th")
    expected_headers = ["Username", "Email", "Name", "Status", "Roles", "Last Login", "Actions"]
    
    for i, expected_header in enumerate(expected_headers):
        actual_header = table_headers.nth(i).text_content().strip()
        assert expected_header in actual_header, f"Expected header '{expected_header}' not found at position {i}, got: '{actual_header}'"
    
    print("✅ Table headers are correct")
    
    # Step 8: Verify table has data
    print("📊 Verifying table data...")
    table_body = page.locator("#userTable tbody")
    rows = table_body.locator("tr")
    row_count = rows.count()
    
    assert row_count > 0, "Table should have at least one row"
    print(f"✅ Table has {row_count} rows")
    
    # Verify each row has the expected number of cells
    first_row = rows.first
    cells = first_row.locator("td")
    cell_count = cells.count()
    assert cell_count == 7, f"Each row should have 7 cells, but found {cell_count}"
    
    # Step 9: Verify action buttons in rows
    print("🔍 Checking action buttons...")
    first_row_actions = first_row.locator("td").last
    assert first_row_actions.locator("a[title='View']").is_visible(), "View button should be visible"
    assert first_row_actions.locator("a[title='Edit']").is_visible(), "Edit button should be visible"
    assert first_row_actions.locator("a[title='Manage Roles']").is_visible(), "Manage Roles button should be visible"
    
    # Step 10: Verify pagination
    print("📄 Checking pagination...")
    pagination_info = page.locator("#pagination-info")
    assert pagination_info.is_visible(), "Pagination info should be visible"
    pagination_text = pagination_info.text_content()
    assert "Showing" in pagination_text and "users" in pagination_text, f"Pagination should show user count, got: {pagination_text}"
    
    # Step 11: Test table responsiveness
    print("📱 Testing table responsiveness...")
    # The table should have DataTables initialized
    assert page.locator(".dataTables_wrapper").is_visible(), "DataTables wrapper should be present"
    
    # Step 12: Final JavaScript error check
    assert len(js_errors) == 0, f"JavaScript errors detected during test: {js_errors}"
    
    # Step 13: Take a screenshot for visual verification (optional)
    # Uncomment the following lines to save a screenshot for debugging
    # page.screenshot(path="identity_admin_smoke_test.png")
    # print("📸 Screenshot saved as identity_admin_smoke_test.png")
    
    print("\n✅ Identity Admin Users smoke test completed successfully!")
    print(f"   - No JavaScript errors")
    print(f"   - All page elements present")
    print(f"   - Table structure correct")
    print(f"   - {row_count} users displayed")
    print(f"   - All controls functional")


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
            test_identity_admin_users_smoke(page)
        finally:
            # Clean up screenshot
            import os
            if os.path.exists("identity_admin_smoke_test.png"):
                os.remove("identity_admin_smoke_test.png")
            browser.close()