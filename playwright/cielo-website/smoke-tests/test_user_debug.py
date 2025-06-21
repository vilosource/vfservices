"""
Debug test to check user context in the website.
"""
import pytest
from playwright.sync_api import Page


def test_debug_user_context(page: Page):
    """Debug test to check user information."""
    
    # Login as admin
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_function("!window.location.href.includes('/accounts/login')", timeout=10000)
    
    # Execute some JavaScript to check the user context
    user_info = page.evaluate("""
        () => {
            // Get the user dropdown text
            const userDropdown = document.querySelector('.nav-user .pro-user-name');
            const username = userDropdown ? userDropdown.textContent.trim() : 'Not found';
            
            // Get welcome message
            const welcomeMsg = document.querySelector('.dropdown-header h6');
            const welcome = welcomeMsg ? welcomeMsg.textContent.trim() : 'Not found';
            
            return {
                username: username,
                welcome: welcome,
                userId: window.USER_ID || 'Not available',
                userRoles: window.USER_ROLES || 'Not available'
            };
        }
    """)
    
    print(f"\nUser Context Debug:")
    print(f"  Username displayed: {user_info['username']}")
    print(f"  Welcome message: {user_info['welcome']}")
    print(f"  User ID (if exposed): {user_info['userId']}")
    print(f"  User Roles (if exposed): {user_info['userRoles']}")
    
    # Check cookies
    cookies = page.context.cookies()
    jwt_cookie = next((c for c in cookies if c['name'] == 'jwt'), None)
    print(f"\n  JWT Cookie exists: {jwt_cookie is not None}")
    
    # Check if we can access the admin page directly
    print("\nTrying to access /admin/ directly...")
    response = page.goto("https://website.vfservices.viloforge.com/admin/", wait_until="domcontentloaded")
    print(f"  Status: {response.status}")
    print(f"  URL after navigation: {page.url}")
    
    if response.status == 200:
        print("  ✅ Can access /admin/ directly")
    else:
        print("  ❌ Cannot access /admin/ directly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])