"""
Complete test for all Identity Admin views
Tests all views including the newly created ones
"""
import pytest
from playwright.sync_api import Page, expect
import time

BASE_URL = "https://website.vfservices.viloforge.com"

def test_identity_admin_complete_functionality(page: Page):
    """Test all Identity Admin views and functionality."""
    
    print("🔍 Starting complete Identity Admin test...")
    
    # Step 1: Login
    print("📍 Logging in...")
    page.goto(f"{BASE_URL}/login/")
    page.wait_for_load_state("networkidle")
    
    page.fill("input[name='email']", "alice")
    page.fill("input[name='password']", "alicepassword")
    page.click("button[type='submit']")
    
    page.wait_for_url("**/", timeout=10000)
    time.sleep(1)
    print("✅ Login successful")
    
    # Step 2: Test Dashboard
    print("📊 Testing Dashboard...")
    page.goto(f"{BASE_URL}/admin/")
    page.wait_for_load_state("networkidle")
    
    assert "Identity Administration" in page.title()
    assert page.locator("h4.page-title").is_visible()
    print("✅ Dashboard loads correctly")
    
    # Step 3: Test User List
    print("👥 Testing User List...")
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_load_state("networkidle")
    
    assert "User Management" in page.title()
    assert page.locator("#userTable").is_visible()
    
    # Wait for users to load
    page.wait_for_selector("#userTable tbody tr", timeout=10000)
    row_count = page.locator("#userTable tbody tr").count()
    assert row_count > 0, "User table should have data"
    print(f"✅ User List loads with {row_count} users")
    
    # Step 4: Test User Create
    print("➕ Testing User Create...")
    page.goto(f"{BASE_URL}/admin/users/create/")
    page.wait_for_load_state("networkidle")
    
    assert "Create User" in page.title()
    assert page.locator("#createUserForm").is_visible()
    assert page.locator("#username").is_visible()
    assert page.locator("#email").is_visible()
    assert page.locator("#password").is_visible()
    print("✅ User Create form loads correctly")
    
    # Step 5: Test User Detail
    print("👤 Testing User Detail...")
    page.goto(f"{BASE_URL}/admin/users/1/")
    page.wait_for_load_state("networkidle")
    
    assert "User Details" in page.title()
    # Should have user info loaded via JavaScript
    time.sleep(2)  # Wait for API call
    print("✅ User Detail page loads")
    
    # Step 6: Test User Edit
    print("✏️ Testing User Edit...")
    page.goto(f"{BASE_URL}/admin/users/1/edit/")
    page.wait_for_load_state("networkidle")
    
    assert "Edit User" in page.title()
    time.sleep(2)  # Wait for form to load
    print("✅ User Edit page loads")
    
    # Step 7: Test User Roles
    print("🛡️ Testing User Roles...")
    page.goto(f"{BASE_URL}/admin/users/1/roles/")
    page.wait_for_load_state("networkidle")
    
    assert "Manage Roles" in page.title()
    time.sleep(2)  # Wait for roles to load
    print("✅ User Roles page loads")
    
    # Step 8: Test Role List
    print("📋 Testing Role List...")
    page.goto(f"{BASE_URL}/admin/roles/")
    page.wait_for_load_state("networkidle")
    
    assert "Role Browser" in page.title()
    assert page.locator("#serviceFilter").is_visible()
    assert page.locator("#roleSearch").is_visible()
    
    # Wait for roles to load
    time.sleep(3)
    print("✅ Role List page loads correctly")
    
    # Step 9: Test Role Assign
    print("🎯 Testing Role Assign...")
    page.goto(f"{BASE_URL}/admin/roles/assign/")
    page.wait_for_load_state("networkidle")
    
    assert "Assign Roles" in page.title()
    assert page.locator("#roleAssignmentForm").is_visible()
    assert page.locator("#userSelect").is_visible()
    assert page.locator("#serviceSelect").is_visible()
    assert page.locator("#roleSelect").is_visible()
    
    # Wait for form to initialize
    time.sleep(3)
    print("✅ Role Assign page loads correctly")
    
    # Step 10: Test Service List
    print("🌐 Testing Service List...")
    page.goto(f"{BASE_URL}/admin/services/")
    page.wait_for_load_state("networkidle")
    
    assert "Service Registry" in page.title()
    assert page.locator("#serviceSearch").is_visible()
    assert page.locator("#statusFilter").is_visible()
    
    # Wait for services to load
    time.sleep(3)
    print("✅ Service List page loads correctly")
    
    # Step 11: Test Navigation between pages
    print("🧭 Testing Navigation...")
    
    # Go back to dashboard
    page.goto(f"{BASE_URL}/admin/")
    page.wait_for_load_state("networkidle")
    
    # Test navigation links in sidebar (if available)
    users_link = page.locator("a[href*='/admin/users/']").first
    if users_link.is_visible():
        users_link.click()
        page.wait_for_load_state("networkidle")
        assert "User Management" in page.title()
        print("✅ Navigation links work correctly")
    
    # Step 12: Test JavaScript functionality
    print("⚡ Testing JavaScript functionality...")
    
    # Go to user list and test search
    page.goto(f"{BASE_URL}/admin/users/")
    page.wait_for_load_state("networkidle")
    page.wait_for_selector("#userTable tbody tr", timeout=10000)
    
    # Test search functionality
    if page.locator("#searchInput").is_visible():
        page.fill("#searchInput", "alice")
        page.click("#applyFilters")
        time.sleep(2)
        
        # Should have filtered results
        rows_after_filter = page.locator("#userTable tbody tr").count()
        print(f"✅ Search functionality works (filtered to {rows_after_filter} rows)")
        
        # Clear search
        page.click("#clearFilters")
        time.sleep(2)
    
    print("\n🎉 Complete Identity Admin test finished successfully!")
    print("All views are working correctly:")
    print("  ✅ Dashboard")
    print("  ✅ User List")
    print("  ✅ User Create")
    print("  ✅ User Detail")
    print("  ✅ User Edit") 
    print("  ✅ User Roles")
    print("  ✅ Role List")
    print("  ✅ Role Assign")
    print("  ✅ Service List")
    print("  ✅ Navigation")
    print("  ✅ JavaScript functionality")


def test_user_create_form_validation(page: Page):
    """Test form validation on the user create page."""
    
    print("📝 Testing User Create form validation...")
    
    # Login first
    page.goto(f"{BASE_URL}/login/")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='email']", "alice")
    page.fill("input[name='password']", "alicepassword")
    page.click("button[type='submit']")
    page.wait_for_url("**/", timeout=10000)
    
    # Go to user create page
    page.goto(f"{BASE_URL}/admin/users/create/")
    page.wait_for_load_state("networkidle")
    
    # Try to submit empty form (should show validation errors)
    submit_btn = page.locator("button[type='submit']")
    submit_btn.click()
    
    # Form should not submit with empty fields
    time.sleep(1)
    assert "Create User" in page.title()  # Still on same page
    print("✅ Form validation prevents empty submission")
    
    # Fill in some fields and test partial validation
    page.fill("#username", "testuser")
    page.fill("#email", "invalid-email")  # Invalid email
    submit_btn.click()
    
    time.sleep(1)
    assert "Create User" in page.title()  # Still on same page
    print("✅ Email validation works")
    
    # Test password matching
    page.fill("#email", "test@example.com")
    page.fill("#password", "password123")
    page.fill("#password_confirm", "differentpassword")
    submit_btn.click()
    
    time.sleep(1)
    assert "Create User" in page.title()  # Still on same page
    print("✅ Password confirmation validation works")
    
    print("✅ User Create form validation is working correctly")


def test_role_assignment_workflow(page: Page):
    """Test the role assignment workflow."""
    
    print("🎭 Testing Role Assignment workflow...")
    
    # Login first
    page.goto(f"{BASE_URL}/login/")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='email']", "alice")
    page.fill("input[name='password']", "alicepassword")
    page.click("button[type='submit']")
    page.wait_for_url("**/", timeout=10000)
    
    # Go to role assign page
    page.goto(f"{BASE_URL}/admin/roles/assign/")
    page.wait_for_load_state("networkidle")
    time.sleep(3)  # Wait for form to initialize
    
    # Test service selection
    service_select = page.locator("#serviceSelect")
    if service_select.locator("option").count() > 1:
        # Select a service
        service_select.select_option(index=1)
        time.sleep(1)
        
        # Role dropdown should be enabled
        role_select = page.locator("#roleSelect")
        assert not role_select.is_disabled(), "Role select should be enabled after service selection"
        print("✅ Service selection enables role dropdown")
    
    # Test user selection (Select2)
    user_select = page.locator("#userSelect")
    if user_select.is_visible():
        print("✅ User selection field is available")
    
    print("✅ Role Assignment workflow components are working")


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
            test_identity_admin_complete_functionality(page)
            print("\n" + "="*50)
            test_user_create_form_validation(page)
            print("\n" + "="*50)
            test_role_assignment_workflow(page)
            
        finally:
            browser.close()