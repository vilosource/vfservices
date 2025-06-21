"""
Test Identity Admin User Detail Page functionality
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://website.vfservices.viloforge.com"


def test_user_detail_page_loads(page: Page):
    """Test that the user detail page loads correctly and displays user information."""
    
    # Enable console logging
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
    
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
    
    # Find a user with a valid ID (not 0)
    rows = page.locator("#userTable tbody tr")
    view_button = None
    user_detail_url = None
    
    # Look for a user with ID > 0
    for i in range(min(5, rows.count())):  # Check first 5 rows
        row = rows.nth(i)
        btn = row.locator("a[title='View']")
        href = btn.get_attribute("href")
        if href and "/users/0/" not in href:
            view_button = btn
            user_detail_url = href
            break
    
    if not view_button:
        # Fallback to first row
        first_row = rows.first
        view_button = first_row.locator("a[title='View']")
        user_detail_url = view_button.get_attribute("href")
    
    print(f"Clicking on user detail URL: {user_detail_url}")
    
    # Click the view button
    view_button.click()
    
    # Wait for navigation to user detail page
    page.wait_for_url("**/users/*/", timeout=10000)
    
    # Take screenshot immediately after navigation
    page.screenshot(path="user_detail_initial.png")
    print(f"Current URL: {page.url}")
    
    # Wait for loading spinner to disappear OR error message to appear
    try:
        page.wait_for_selector("#loading-spinner", state="hidden", timeout=10000)
    except:
        # Check if there's an error message
        if page.locator("#error-message").is_visible():
            error_text = page.locator("#error-message").text_content()
            print(f"Error loading user details: {error_text}")
            assert False, f"User detail page showed error: {error_text}"
    
    # Check that user details are displayed OR error message
    if page.locator("#error-message").is_visible():
        error_text = page.locator("#error-message").text_content()
        print(f"Error: {error_text}")
        assert False, f"User detail page showed error: {error_text}"
    
    page.wait_for_selector("#user-details", state="visible", timeout=10000)
    
    # Debug: check what's visible
    page.screenshot(path="user_detail_after_load.png")
    print(f"User details visible: {page.locator('#user-details').is_visible()}")
    print(f"Loading spinner visible: {page.locator('#loading-spinner').is_visible()}")
    print(f"Error message visible: {page.locator('#error-message').is_visible()}")
    
    # Verify key elements are present
    assert page.locator("#user-fullname").is_visible(), "User full name should be visible"
    assert page.locator("#user-username").is_visible(), "Username should be visible"
    assert page.locator("#user-email").is_visible(), "Email should be visible"
    assert page.locator("#user-status").is_visible(), "Status should be visible"
    
    # Check that action buttons are present (in the page actions area)
    assert page.locator("#edit-user-btn").is_visible(), "Edit User button should be visible"
    assert page.locator("#manage-roles-btn").is_visible(), "Manage Roles button should be visible"
    assert page.locator("a:has-text('Back to List')").is_visible(), "Back to List button should be visible"
    
    # Check that roles section is present
    assert page.locator("h5:has-text('Assigned Roles')").is_visible(), "Roles section should be visible"
    
    # Take screenshot for debugging
    page.screenshot(path="identity_admin_user_detail.png")
    
    # Get some actual values for verification
    username = page.locator("#user-username").text_content()
    email = page.locator("#user-email").text_content()
    print(f"✅ User detail page loaded successfully for user: {username} ({email})")
    
    # Test navigation back to list
    page.click("a:has-text('Back to List')")
    page.wait_for_url("**/users/", timeout=5000)
    print("✅ Successfully navigated back to user list")


def test_user_detail_error_handling(page: Page):
    """Test that user detail page handles non-existent users gracefully."""
    
    # Check if we're already logged in by checking current URL
    if "/login" in page.url:
        # Login first
        page.goto(f"{BASE_URL}/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='email']", "alice")
        page.fill("input[name='password']", "alicepassword")
        page.click("button[type='submit']")
        page.wait_for_url("**/", timeout=10000)
        time.sleep(1)
    
    # Try to access a non-existent user
    page.goto(f"{BASE_URL}/admin/users/99999/")
    page.wait_for_load_state("networkidle")
    
    # Should show error message
    error_message = page.wait_for_selector("#error-message", state="visible", timeout=10000)
    assert error_message.is_visible(), "Error message should be displayed for non-existent user"
    
    error_text = error_message.text_content()
    print(f"✅ Error handling works: {error_text}")


def test_user_detail_navigation_buttons(page: Page):
    """Test that navigation buttons on user detail page work correctly."""
    
    # Check if we're already logged in
    if "/login" in page.url:
        # Login and navigate to user detail page
        page.goto(f"{BASE_URL}/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='email']", "alice")
        page.fill("input[name='password']", "alicepassword")
        page.click("button[type='submit']")
        page.wait_for_url("**/", timeout=10000)
        time.sleep(1)
    
    # Navigate to users list
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_selector("#userTable", state="visible", timeout=10000)
    
    # Click on first user's view button
    first_row = page.locator("#userTable tbody tr").first
    first_row.locator("a[title='View']").click()
    page.wait_for_url("**/users/*/", timeout=10000)
    page.wait_for_selector("#user-details", state="visible", timeout=10000)
    
    # Test Edit User button
    edit_button = page.locator("#edit-user-btn")
    edit_url = edit_button.get_attribute("href")
    edit_button.click()
    page.wait_for_url("**/users/*/edit/", timeout=10000)
    print("✅ Edit User button works")
    
    # Go back to detail page
    page.go_back()
    page.wait_for_selector("#user-details", state="visible", timeout=10000)
    
    # Test Manage Roles button
    roles_button = page.locator("#manage-roles-btn")
    roles_url = roles_button.get_attribute("href")
    roles_button.click()
    page.wait_for_url("**/users/*/roles/", timeout=10000)
    print("✅ Manage Roles button works")
    
    # All navigation tests passed
    print("✅ All user detail navigation buttons work correctly")


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
            print("Testing user detail page loads...")
            test_user_detail_page_loads(page)
            print("✅ test_user_detail_page_loads PASSED")
            
            print("\nTesting error handling...")
            test_user_detail_error_handling(page)
            print("✅ test_user_detail_error_handling PASSED")
            
            print("\nTesting navigation buttons...")
            test_user_detail_navigation_buttons(page)
            print("✅ test_user_detail_navigation_buttons PASSED")
            
            print("\n✅ All user detail page tests passed!")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="test_failure.png")
            # Don't re-raise to see which test failed
        finally:
            browser.close()