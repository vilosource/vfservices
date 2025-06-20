"""
Debug test to investigate CIELO logout issue.
"""
from playwright.sync_api import sync_playwright
import json


def test_cielo_logout_debug():
    """Debug test to investigate logout cookie behavior"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Run headless
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        print("\n=== CIELO Logout Debug Test ===")
        
        # Step 1: Login
        print("\n1. Logging in...")
        page.goto("https://cielo.viloforge.com/accounts/login/")
        page.fill('input[name="email"]', 'alice')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        print(f"   Current URL after login: {page.url}")
        
        # Get cookies after login
        cookies = context.cookies()
        print("\n2. Cookies after login:")
        for cookie in cookies:
            if 'jwt' in cookie['name']:
                print(f"   {cookie['name']}:")
                print(f"     domain: {cookie['domain']}")
                print(f"     path: {cookie['path']}")
                print(f"     httpOnly: {cookie['httpOnly']}")
                print(f"     secure: {cookie['secure']}")
                print(f"     sameSite: {cookie.get('sameSite', 'None')}")
                print(f"     value: {cookie['value'][:20]}..." if cookie['value'] else "     value: [EMPTY]")
        
        # Step 2: Navigate to logout
        print("\n3. Navigating to logout page...")
        page.goto("https://cielo.viloforge.com/accounts/logout/")
        print(f"   Current URL: {page.url}")
        
        # Step 3: Click logout button
        print("\n4. Clicking logout button...")
        
        # Intercept the network request to see what happens
        def handle_response(response):
            if response.url.endswith('/logout/'):
                print(f"\n   Logout response:")
                print(f"     Status: {response.status}")
                print(f"     All Headers:")
                for key, value in response.headers.items():
                    print(f"       {key}: {value}")
                
                # Check specifically for Set-Cookie headers
                print(f"\n     Looking for Set-Cookie headers...")
                all_headers = response.all_headers()
                cookie_headers = [h for h in all_headers if h['name'].lower() == 'set-cookie']
                if cookie_headers:
                    print(f"     Found {len(cookie_headers)} Set-Cookie headers:")
                    for h in cookie_headers:
                        print(f"       {h['value']}")
                else:
                    print("     NO Set-Cookie headers found!")
                
        page.on("response", handle_response)
        
        # Click the button
        page.click('button:has-text("Yes, Logout")')
        page.wait_for_load_state("networkidle")
        
        print(f"\n   Redirected to: {page.url}")
        
        # Step 4: Check cookies after logout
        cookies_after = context.cookies()
        print("\n5. Cookies after logout:")
        jwt_found = False
        for cookie in cookies_after:
            if 'jwt' in cookie['name']:
                jwt_found = True
                print(f"   {cookie['name']}:")
                print(f"     domain: {cookie['domain']}")
                print(f"     path: {cookie['path']}")
                print(f"     value: {cookie['value'][:20]}..." if cookie['value'] else "     value: [EMPTY]")
                print(f"     expires: {cookie.get('expires', 'N/A')}")
        
        if not jwt_found:
            print("   No JWT cookies found (good!)")
        
        # Step 5: Try to access protected page
        print("\n6. Testing access after logout...")
        page.goto("https://cielo.viloforge.com/")
        print(f"   Redirected to: {page.url}")
        
        if "/login" in page.url or "/accounts/login/" in page.url:
            print("   ✓ Successfully logged out - redirected to login")
        else:
            print("   ✗ Still logged in - NOT redirected to login")
            
            # Check if we can see user info
            try:
                user_info = page.locator('text=/alice/i').count()
                if user_info > 0:
                    print("   ✗ User info still visible on page")
            except:
                pass
        
        # Step 6: Manual cookie check via JavaScript
        print("\n7. JavaScript cookie check:")
        js_cookies = page.evaluate("document.cookie")
        print(f"   document.cookie: {js_cookies}")
        
        # Don't wait in headless mode
        # input("\nPress Enter to close browser...")
        
        browser.close()


def test_cielo_logout_network_trace():
    """Test with network tracing to see all requests/responses"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            ignore_https_errors=True,
            record_har_path="cielo_logout.har",
            record_har_url_filter="**/cielo.viloforge.com/**"
        )
        page = context.new_page()
        
        print("\n=== CIELO Logout Network Trace ===")
        
        # Quick login
        page.goto("https://cielo.viloforge.com/accounts/login/")
        page.fill('input[name="email"]', 'alice')
        page.fill('input[name="password"]', 'password123')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        
        # Logout
        page.goto("https://cielo.viloforge.com/accounts/logout/")
        
        # Capture the form data
        form_data = page.evaluate("""
            () => {
                const form = document.querySelector('form');
                const formData = new FormData(form);
                const data = {};
                for (let [key, value] of formData.entries()) {
                    data[key] = value;
                }
                return data;
            }
        """)
        print(f"\nForm data: {json.dumps(form_data, indent=2)}")
        
        # Submit logout
        page.click('button:has-text("Yes, Logout")')
        page.wait_for_load_state("networkidle")
        
        # Close context to save HAR file
        context.close()
        browser.close()
        
        print("\nNetwork trace saved to cielo_logout.har")
        print("You can analyze it with: https://toolbox.googleapps.com/apps/har_analyzer/")


if __name__ == "__main__":
    test_cielo_logout_debug()
    # test_cielo_logout_network_trace()