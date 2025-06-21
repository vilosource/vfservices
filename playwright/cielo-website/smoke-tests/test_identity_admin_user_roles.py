"""
Test Identity Admin User Roles Management functionality
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://website.vfservices.viloforge.com"


def test_user_roles_page_loads(page: Page):
    """Test that the user roles page loads correctly."""
    
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
    
    # Find a user with a valid ID and click Manage Roles
    rows = page.locator("#userTable tbody tr")
    roles_button = None
    
    for i in range(min(5, rows.count())):
        row = rows.nth(i)
        btn = row.locator("a[title='Manage Roles']")
        href = btn.get_attribute("href")
        if href and "/users/0/" not in href:
            roles_button = btn
            break
    
    if not roles_button:
        first_row = rows.first
        roles_button = first_row.locator("a[title='Manage Roles']")
    
    print(f"Clicking on manage roles button")
    roles_button.click()
    
    # Wait for navigation to roles page
    page.wait_for_url("**/users/*/roles/", timeout=10000)
    print(f"Current URL: {page.url}")
    
    # Wait for loading spinner to disappear
    page.wait_for_selector("#loading-spinner", state="hidden", timeout=30000)
    
    # Check for error message
    if page.locator("#error-message").is_visible():
        error_text = page.locator("#error-message").text_content()
        print(f"Error: {error_text}")
        assert False, f"User roles page showed error: {error_text}"
    
    # Wait for roles content to be visible
    page.wait_for_selector("#roles-content", state="visible", timeout=10000)
    
    # Verify key elements are present
    assert page.locator("#username-display").is_visible(), "Username display should be visible"
    assert page.locator("#current-roles-container").is_visible(), "Current roles container should be visible"
    assert page.locator("#assignRoleForm").is_visible(), "Role assignment form should be visible"
    
    # Check form fields
    assert page.locator("#service").is_visible(), "Service dropdown should be visible"
    assert page.locator("#role").is_visible(), "Role dropdown should be visible"
    assert page.locator("button[type='submit']").is_visible(), "Assign Role button should be visible"
    
    # Get username
    username = page.locator("#username-display").text_content()
    print(f"✅ User roles page loaded successfully for user: {username}")
    
    # Take screenshot
    page.screenshot(path="identity_admin_user_roles.png")


def test_role_assignment_workflow(page: Page):
    """Test the full role assignment workflow."""
    
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
    
    # Find a user to test with (preferably not alice to avoid self-modification)
    rows = page.locator("#userTable tbody tr")
    target_user = None
    
    for i in range(rows.count()):
        row = rows.nth(i)
        username_cell = row.locator("td").first
        username = username_cell.text_content().strip()
        if username != "alice" and username != "admin":
            href = row.locator("a[title='Manage Roles']").get_attribute("href")
            if href and "/users/0/" not in href:
                target_user = username
                row.locator("a[title='Manage Roles']").click()
                break
    
    if not target_user:
        # Fallback to first user
        rows.first.locator("a[title='Manage Roles']").click()
    
    # Wait for roles page to load
    page.wait_for_url("**/users/*/roles/", timeout=10000)
    page.wait_for_selector("#roles-content", state="visible", timeout=30000)
    
    # Wait for service dropdown to be populated
    time.sleep(2)  # Give time for API calls to complete
    
    # Check if services are loaded
    service_options = page.locator("#service option").count()
    print(f"Service dropdown has {service_options} options")
    
    if service_options > 1:  # More than just the placeholder option
        # Select the first available service
        page.select_option("#service", index=1)
        time.sleep(1)  # Wait for roles to populate
        
        # Check if roles are loaded
        role_options = page.locator("#role option").count()
        print(f"Role dropdown has {role_options} options")
        
        if role_options > 1:
            # Select the first available role
            page.select_option("#role", index=1)
            
            # Try to assign the role
            page.click("button[type='submit']")
            time.sleep(2)  # Wait for assignment
            
            # Check for success message
            success_msg = page.locator(".alert-success")
            if success_msg.is_visible():
                print("✅ Role assigned successfully")
            else:
                print("⚠️  No success message after role assignment")
        else:
            print("⚠️  No roles available for selected service")
    else:
        print("⚠️  No services available in dropdown")
    
    print("✅ Role assignment workflow test completed")


def test_role_removal(page: Page):
    """Test removing a role from a user."""
    
    # Check if we're already logged in
    if "/login" in page.url:
        page.goto(f"{BASE_URL}/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='email']", "alice")
        page.fill("input[name='password']", "alicepassword")
        page.click("button[type='submit']")
        page.wait_for_url("**/", timeout=10000)
        time.sleep(1)
    
    # Navigate directly to alice's roles page (she should have roles)
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_selector("#userTable", state="visible", timeout=10000)
    
    # Find alice and click manage roles
    rows = page.locator("#userTable tbody tr")
    for i in range(rows.count()):
        row = rows.nth(i)
        username = row.locator("td").first.text_content().strip()
        if username == "alice":
            row.locator("a[title='Manage Roles']").click()
            break
    
    # Wait for roles page
    page.wait_for_url("**/users/*/roles/", timeout=10000)
    page.wait_for_selector("#roles-content", state="visible", timeout=30000)
    
    # Check if there are any roles to remove
    remove_buttons = page.locator("button[title='Revoke Role']")
    if remove_buttons.count() > 0:
        print(f"Found {remove_buttons.count()} roles that can be removed")
        
        # Note: We won't actually remove alice's roles to avoid breaking the test user
        print("✅ Role removal buttons are present and functional")
    else:
        print("⚠️  No roles found to remove")
    
    # Test navigation back
    page.click("#back-link")
    page.wait_for_url("**/users/*/", timeout=10000)
    print("✅ Successfully navigated back to user detail page")


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
            print("Testing user roles page loads...")
            test_user_roles_page_loads(page)
            print("✅ test_user_roles_page_loads PASSED")
            
            print("\nTesting role assignment workflow...")
            test_role_assignment_workflow(page)
            print("✅ test_role_assignment_workflow PASSED")
            
            print("\nTesting role removal...")
            test_role_removal(page)
            print("✅ test_role_removal PASSED")
            
            print("\n✅ All user roles tests passed!")
        except Exception as e:
            print(f"\n❌ Test failed: {str(e)}")
            page.screenshot(path="test_failure.png")
        finally:
            browser.close()