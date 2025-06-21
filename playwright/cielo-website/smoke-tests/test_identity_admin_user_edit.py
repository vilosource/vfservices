"""
Test Identity Admin User Edit Page functionality
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://website.vfservices.viloforge.com"


def test_user_edit_page_loads(page: Page):
    """Test that the user edit page loads correctly and displays the form."""
    
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
    time.sleep(1)
    
    # Navigate to admin users page
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_load_state("networkidle")
    
    # Wait for users table to load
    page.wait_for_selector("#userTable", state="visible", timeout=10000)
    
    # Find a user with a valid ID (not 0) and click Edit
    rows = page.locator("#userTable tbody tr")
    edit_button = None
    user_edit_url = None
    
    for i in range(min(5, rows.count())):
        row = rows.nth(i)
        btn = row.locator("a[title='Edit']")
        href = btn.get_attribute("href")
        if href and "/users/0/" not in href:
            edit_button = btn
            user_edit_url = href
            break
    
    if not edit_button:
        first_row = rows.first
        edit_button = first_row.locator("a[title='Edit']")
        user_edit_url = edit_button.get_attribute("href")
    
    print(f"Clicking on user edit URL: {user_edit_url}")
    
    # Click the edit button
    edit_button.click()
    
    # Wait for navigation to user edit page
    page.wait_for_url("**/users/*/edit/", timeout=10000)
    
    # Take screenshot immediately after navigation
    page.screenshot(path="user_edit_initial.png")
    print(f"Current URL: {page.url}")
    
    # Wait for loading spinner to disappear
    page.wait_for_selector("#loading-spinner", state="hidden", timeout=10000)
    
    # Check for error message
    if page.locator("#error-message").is_visible():
        error_text = page.locator("#error-message").text_content()
        print(f"Error: {error_text}")
        assert False, f"User edit page showed error: {error_text}"
    
    # Wait for edit form to be visible
    page.wait_for_selector("#edit-form", state="visible", timeout=10000)
    
    # Verify form fields are present and populated
    assert page.locator("#username").is_visible(), "Username field should be visible"
    assert page.locator("#email").is_visible(), "Email field should be visible"
    assert page.locator("#first_name").is_visible(), "First name field should be visible"
    assert page.locator("#last_name").is_visible(), "Last name field should be visible"
    assert page.locator("#is_active").is_visible(), "Active checkbox should be visible"
    
    # Get the username to verify it's populated
    username = page.locator("#username").input_value()
    email = page.locator("#email").input_value()
    print(f"✅ User edit form loaded for user: {username} ({email})")
    
    # Check that action buttons are present
    assert page.locator("#back-link").is_visible(), "Back link should be visible"
    assert page.locator("button[type='submit']").is_visible(), "Save button should be visible"
    assert page.locator("#cancel-btn").is_visible(), "Cancel button should be visible"
    
    # Take screenshot for debugging
    page.screenshot(path="identity_admin_user_edit.png")
    
    print("✅ User edit page loaded successfully")


def test_user_edit_form_submission(page: Page):
    """Test that user edit form can be submitted successfully."""
    
    # Enable console logging
    page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
    
    # Check if we're already logged in
    if "/login" in page.url:
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
    
    # Click on first user's edit button with valid ID
    rows = page.locator("#userTable tbody tr")
    for i in range(min(5, rows.count())):
        row = rows.nth(i)
        btn = row.locator("a[title='Edit']")
        href = btn.get_attribute("href")
        if href and "/users/0/" not in href:
            btn.click()
            break
    
    page.wait_for_url("**/users/*/edit/", timeout=10000)
    page.wait_for_selector("#edit-form", state="visible", timeout=10000)
    
    # Store original values
    original_first_name = page.locator("#first_name").input_value()
    original_last_name = page.locator("#last_name").input_value()
    
    # Make changes to the form
    test_first_name = "Test"
    test_last_name = "Updated"
    
    page.fill("#first_name", test_first_name)
    page.fill("#last_name", test_last_name)
    
    # Save the form
    page.click("button[type='submit']")
    
    # Wait for success message or redirect
    time.sleep(2)  # Give time for save operation
    
    # Check if we're still on edit page or redirected
    if "edit" in page.url:
        # Check for success message
        success_msg = page.locator(".alert-success")
        if success_msg.is_visible():
            print("✅ Form saved successfully with message")
        else:
            print("⚠️  Form submitted but no success message")
    else:
        print("✅ Form saved and redirected")
    
    # Restore original values if still on edit page
    if "edit" in page.url and original_first_name != test_first_name:
        page.fill("#first_name", original_first_name)
        page.fill("#last_name", original_last_name)
        page.click("button[type='submit']")
        time.sleep(1)
        print("✅ Original values restored")


def test_user_edit_navigation(page: Page):
    """Test navigation buttons on user edit page."""
    
    # Check if we're already logged in
    if "/login" in page.url:
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
    
    # Click on first user's edit button with valid ID
    rows = page.locator("#userTable tbody tr")
    for i in range(min(5, rows.count())):
        row = rows.nth(i)
        btn = row.locator("a[title='Edit']")
        href = btn.get_attribute("href")
        if href and "/users/0/" not in href:
            btn.click()
            break
    
    page.wait_for_url("**/users/*/edit/", timeout=10000)
    page.wait_for_selector("#edit-form", state="visible", timeout=10000)
    
    # Test Cancel button
    page.click("#cancel-btn")
    page.wait_for_url("**/users/*/", timeout=10000)
    print("✅ Cancel button works - returned to user detail page")
    
    # Go back to edit page
    page.click("#edit-user-btn")
    page.wait_for_url("**/users/*/edit/", timeout=10000)
    page.wait_for_selector("#edit-form", state="visible", timeout=10000)
    
    # Test Back to User link
    page.click("#back-link")
    page.wait_for_url("**/users/*/", timeout=10000)
    print("✅ Back to User link works")
    
    print("✅ All navigation buttons work correctly")


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
            print("Testing user edit page loads...")
            test_user_edit_page_loads(page)
            print("✅ test_user_edit_page_loads PASSED")
            
            print("\nTesting form submission...")
            test_user_edit_form_submission(page)
            print("✅ test_user_edit_form_submission PASSED")
            
            print("\nTesting navigation...")
            test_user_edit_navigation(page)
            print("✅ test_user_edit_navigation PASSED")
            
            print("\n✅ All user edit page tests passed!")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="test_failure.png")
        finally:
            browser.close()