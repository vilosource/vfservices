"""Test avatar functionality across all Django applications."""

from playwright.sync_api import Page, sync_playwright
import time


def test_avatar_on_app(page: Page, app_name: str, app_url: str):
    """Test avatar loading on a specific Django app."""
    print(f"\n{'='*50}")
    print(f"Testing {app_name}")
    print(f"{'='*50}")
    
    # Login
    page.goto(f"{app_url}/accounts/login/")
    page.wait_for_load_state('networkidle')
    
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    
    # Wait for redirect
    page.wait_for_url(app_url + "/", timeout=10000)
    time.sleep(2)  # Allow avatar to load
    
    # Check if AvatarManager is loaded
    avatar_manager_exists = page.evaluate("typeof AvatarManager !== 'undefined'")
    print(f"AvatarManager loaded: {avatar_manager_exists}")
    
    # Check avatar src
    avatar_elements = page.locator('img.user-avatar').all()
    print(f"Found {len(avatar_elements)} avatar element(s)")
    
    for i, element in enumerate(avatar_elements):
        src = element.get_attribute('src')
        print(f"Avatar {i+1} src: {src}")
    
    # Verify at least one avatar is loaded
    if avatar_elements:
        first_avatar_src = avatar_elements[0].get_attribute('src')
        if '/avatar-2.jpg' in first_avatar_src:
            print("✓ Avatar loaded correctly (avatar-2.jpg for admin user)")
        else:
            print(f"✗ Unexpected avatar: {first_avatar_src}")
    
    # Take screenshot
    page.screenshot(path=f"{app_name}_avatar.png")
    print(f"Screenshot saved as {app_name}_avatar.png")


def main():
    """Test avatars on all three Django applications."""
    apps = [
        ("website", "https://website.vfservices.viloforge.com"),
        ("cielo-website", "https://cielo.viloforge.com"),
        ("maltacentral-web", "https://www.maltacentral.com")
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for app_name, app_url in apps:
            context = browser.new_context()
            page = context.new_page()
            
            try:
                test_avatar_on_app(page, app_name, app_url)
            except Exception as e:
                print(f"Error testing {app_name}: {e}")
            finally:
                context.close()
        
        browser.close()
    
    print(f"\n{'='*50}")
    print("Avatar testing complete!")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()