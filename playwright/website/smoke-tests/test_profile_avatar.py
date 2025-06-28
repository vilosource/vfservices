"""Test avatar display on profile page."""

from playwright.sync_api import Page
import time


def test_profile_page_avatar(page: Page):
    """Test that avatar loads correctly on profile page."""
    
    # Login first
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    page.wait_for_load_state('networkidle')
    
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    
    # Wait for redirect to home
    page.wait_for_url("https://website.vfservices.viloforge.com/", timeout=10000)
    
    # Now go to profile page
    page.goto("https://website.vfservices.viloforge.com/accounts/profile/")
    page.wait_for_load_state('networkidle')
    
    # Wait a bit for JavaScript to execute
    time.sleep(3)
    
    # Check if avatar-management.js is loaded
    avatar_manager_exists = page.evaluate("typeof AvatarManager !== 'undefined'")
    print(f"AvatarManager loaded on profile page: {avatar_manager_exists}")
    
    # Check the avatar src
    avatar_src = page.locator('img.user-avatar').first.get_attribute('src')
    print(f"Avatar src on profile page: {avatar_src}")
    
    # Check if avatar was initialized
    if avatar_manager_exists:
        avatar_config = page.evaluate("AvatarManager.config.identityProviderUrl")
        print(f"AvatarManager configured with: {avatar_config}")
    
    # Take a screenshot
    page.screenshot(path="profile_page_avatar.png")
    
    # Go back to home page to compare
    page.goto("https://website.vfservices.viloforge.com/")
    page.wait_for_load_state('networkidle')
    time.sleep(2)
    
    home_avatar_src = page.locator('img.user-avatar').first.get_attribute('src')
    print(f"Avatar src on home page: {home_avatar_src}")
    
    # Compare
    if avatar_src == home_avatar_src:
        print("✓ Avatars match on both pages")
    else:
        print("✗ Avatars are different!")
        print(f"  Profile: {avatar_src}")
        print(f"  Home: {home_avatar_src}")


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            test_profile_page_avatar(page)
        finally:
            browser.close()