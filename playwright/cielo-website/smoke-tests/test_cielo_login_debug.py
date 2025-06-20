"""Debug test for CIELO login flow"""
import pytest
from playwright.sync_api import sync_playwright

def test_cielo_login_debug():
    """Debug the CIELO login flow step by step"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        # Enable request/response logging
        def log_request(request):
            if request.method == "POST":
                print(f"[REQUEST] {request.method} {request.url}")
        
        def log_response(response):
            if response.url != page.url and (response.status >= 300 and response.status < 400):
                print(f"[REDIRECT] {response.status} from {response.url}")
                headers = response.headers
                if 'location' in headers:
                    print(f"  -> Location: {headers['location']}")
        
        page.on("request", log_request)
        page.on("response", log_response)
        
        try:
            # Step 1: Go to CIELO
            print("\n=== Step 1: Navigate to CIELO ===")
            response = page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            print(f"Initial URL: {page.url}")
            print(f"Title: {page.title()}")
            
            # Step 2: Fill login form
            print("\n=== Step 2: Fill login form ===")
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'password123')
            print("Credentials entered")
            
            # Step 3: Submit form and track navigation
            print("\n=== Step 3: Submit form ===")
            
            # Wait for navigation after clicking submit
            with page.expect_navigation(wait_until="networkidle") as navigation_info:
                page.click('button[type="submit"]')
            
            nav_response = navigation_info.value
            print(f"Navigation completed to: {page.url}")
            print(f"Response status: {nav_response.status if nav_response else 'None'}")
            
            # Step 4: Check where we ended up
            print("\n=== Step 4: Final state ===")
            print(f"Final URL: {page.url}")
            print(f"Final title: {page.title()}")
            
            # Check cookies
            cookies = context.cookies()
            jwt_cookie = next((c for c in cookies if c['name'] == 'jwt'), None)
            if jwt_cookie:
                print(f"JWT cookie set: domain={jwt_cookie['domain']}, has_value={bool(jwt_cookie['value'])}")
            else:
                print("No JWT cookie found")
            
            # Try going back to CIELO explicitly
            print("\n=== Step 5: Navigate back to CIELO ===")
            page.goto("https://cielo.viloforge.com/", wait_until="networkidle")
            print(f"After explicit navigation: {page.url}")
            print(f"Title: {page.title()}")
            
            # Check if we're authenticated on CIELO
            login_elements = page.locator('a[href*="login"]').count()
            logout_elements = page.locator('a[href*="logout"]').count()
            print(f"Login links found: {login_elements}")
            print(f"Logout links found: {logout_elements}")
            
        finally:
            browser.close()

if __name__ == "__main__":
    test_cielo_login_debug()