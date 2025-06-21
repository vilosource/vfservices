"""
Basic setup tests for Identity Admin app
"""
import pytest


def test_identity_admin_dashboard_requires_auth(page, ensure_services_running):
    """Test that identity admin dashboard requires authentication."""
    # Try to access admin dashboard without authentication
    response = page.goto(f"{pytest.HOST_PROJECT_URL}/admin/", wait_until="networkidle")
    
    # Should redirect to login or show forbidden
    assert response.status in [302, 403], "Admin should require authentication"
    
    # If redirected, should go to login page
    if response.status == 302:
        assert "/login" in page.url or "/auth" in page.url


def test_identity_admin_dashboard_loads(authenticated_page, ensure_services_running):
    """Test that authenticated users with identity_admin role can access dashboard."""
    page = authenticated_page
    
    # Navigate to admin dashboard
    response = page.goto(f"{pytest.HOST_PROJECT_URL}/admin/", wait_until="networkidle")
    
    # Check if we can access it (admin user has identity_admin role)
    if response.status == 403:
        # User doesn't have identity_admin role
        assert page.locator("text=identity_admin role required").count() > 0
    else:
        # Should see the dashboard
        assert response.status == 200
        assert page.locator("h4:has-text('Identity Administration')").count() > 0
        
        # Check main navigation items
        assert page.locator("text=User Management").count() > 0
        assert page.locator("text=Role Assignment").count() > 0
        assert page.locator("text=Service Registry").count() > 0


def test_identity_admin_navigation(authenticated_page, ensure_services_running):
    """Test navigation menu in identity admin."""
    page = authenticated_page
    
    # Go to dashboard
    page.goto(f"{pytest.HOST_PROJECT_URL}/admin/", wait_until="networkidle")
    
    # Check sidebar navigation items
    assert page.locator("a:has-text('Dashboard')").count() > 0
    assert page.locator("a:has-text('Users')").count() > 0
    assert page.locator("a:has-text('Roles')").count() > 0
    assert page.locator("a:has-text('Services')").count() > 0
    assert page.locator("a:has-text('Create User')").count() > 0
    assert page.locator("a:has-text('Assign Roles')").count() > 0


def test_user_list_page(authenticated_page, ensure_services_running):
    """Test that user list page loads."""
    page = authenticated_page
    
    # Navigate to users page
    page.goto(f"{pytest.HOST_PROJECT_URL}/admin/users/", wait_until="networkidle")
    
    # Should see user list page
    assert page.locator("h4:has-text('User Management')").count() > 0
    
    # Should have search box
    assert page.locator("input[type='search']").count() > 0
    
    # Should have create user button
    assert page.locator("a:has-text('Add User')").count() > 0


def test_services_page(authenticated_page, ensure_services_running):
    """Test that services page loads and shows registered services."""
    page = authenticated_page
    
    # Navigate to services page
    page.goto(f"{pytest.HOST_PROJECT_URL}/admin/services/", wait_until="networkidle")
    
    # Should see services page
    assert page.locator("h4:has-text('Service Registry')").count() > 0
    
    # Should show some services
    assert page.locator("text=identity_provider").count() > 0


def test_static_files_loading(authenticated_page, ensure_services_running):
    """Test that static files (CSS/JS) are loading correctly."""
    page = authenticated_page
    
    # Track network requests
    css_loaded = False
    js_loaded = False
    
    def handle_response(response):
        nonlocal css_loaded, js_loaded
        if "identity-admin.css" in response.url:
            css_loaded = response.status == 200
        elif "api-client.js" in response.url:
            js_loaded = response.status == 200
    
    page.on("response", handle_response)
    
    # Load dashboard
    page.goto(f"{pytest.HOST_PROJECT_URL}/admin/", wait_until="networkidle")
    
    # Check that our custom files loaded
    assert css_loaded, "identity-admin.css should load successfully"
    assert js_loaded, "api-client.js should load successfully"
    
    # Check that global JS objects are available
    assert page.evaluate("typeof window.identityAdminClient") == "object"
    assert page.evaluate("typeof window.IDENTITY_PROVIDER_URL") == "string"