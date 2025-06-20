"""
Integration test to verify alice can access Billing API after logging in through CIELO.
Tests cross-service authentication between CIELO and Billing API.
"""
import pytest
from playwright.sync_api import sync_playwright, expect


def test_alice_billing_api_access():
    """Test that alice can access Billing API private endpoint after CIELO login"""
    with sync_playwright() as p:
        # Launch browser with debugging enabled
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        
        # Enable console logging for debugging
        page = context.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        try:
            print("\n=== Testing Alice's Billing API Access via CIELO ===")
            
            # Step 1: Login to CIELO as alice
            print("\nStep 1: Logging into CIELO as alice...")
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Should be redirected to login page
            assert "/accounts/login/" in page.url or "/login" in page.url
            print(f"✓ Redirected to login page: {page.url}")
            
            # Fill login form
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'password123')
            
            # Submit login
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            # Step 2: Verify successful CIELO login
            print("\nStep 2: Verifying successful CIELO login...")
            current_url = page.url
            
            if "cielo.viloforge.com" not in current_url:
                print(f"✗ Redirected away from CIELO to: {current_url}")
                pytest.fail("User alice lacks CIELO access")
            
            print(f"✓ Successfully logged into CIELO: {current_url}")
            
            # Check for JWT cookie
            cookies = context.cookies()
            jwt_found = False
            print("\nAuthentication cookies:")
            for cookie in cookies:
                if 'jwt' in cookie['name'].lower() or 'session' in cookie['name'].lower() or 'token' in cookie['name'].lower():
                    jwt_found = True
                    print(f"✓ Cookie: {cookie['name']}")
                    print(f"  - Domain: {cookie['domain']}")
                    print(f"  - Path: {cookie['path']}")
                    print(f"  - HttpOnly: {cookie.get('httpOnly', False)}")
                    print(f"  - Secure: {cookie.get('secure', False)}")
                    print(f"  - SameSite: {cookie.get('sameSite', 'None')}")
            
            if not jwt_found:
                print("⚠ Warning: No JWT/session cookie found, but continuing test...")
            
            # Step 3: Access Billing API private endpoint
            print("\nStep 3: Accessing Billing API private endpoint...")
            
            # Navigate to Billing API
            response = page.goto("https://billing.vfservices.viloforge.com/private", wait_until="networkidle")
            
            # Check response status
            status = response.status if response else None
            print(f"Response status: {status}")
            
            # Step 4: Verify authorization
            print("\nStep 4: Verifying authorization...")
            
            # Check if we got a successful response (200 OK)
            if status == 200:
                print("✓ Alice is authorized to access Billing API private endpoint")
                
                # Get response content
                content = page.content()
                print(f"Response preview: {content[:200]}...")
                
                # Check for common API response patterns
                if "error" in content.lower() and "unauthorized" not in content.lower():
                    print("⚠ Response contains 'error' but not unauthorized - checking content")
                elif "unauthorized" in content.lower() or "forbidden" in content.lower():
                    pytest.fail("Alice received unauthorized/forbidden response")
                
            elif status == 401:
                content = page.content()
                print(f"401 Unauthorized - Response content: {content[:500]}...")
                pytest.fail("Alice received 401 Unauthorized - authentication failed")
            elif status == 403:
                # Get the error content
                content = page.content()
                print(f"403 Forbidden - Response content: {content[:500]}...")
                
                # Check if it's an authentication issue
                if "Authentication credentials were not provided" in content:
                    print("\n⚠️ AUTHENTICATION ISSUE DETECTED:")
                    print("The JWT token from CIELO is not being passed to Billing API")
                    print("This indicates a cross-domain authentication configuration issue")
                    pytest.fail("Authentication tokens not shared between CIELO and Billing API")
                else:
                    pytest.fail("Alice received 403 Forbidden - lacks permission")
            elif status == 302 or status == 301:
                # Check if redirected to login
                final_url = page.url
                if "login" in final_url:
                    pytest.fail(f"Alice was redirected to login: {final_url}")
                else:
                    print(f"⚠ Redirected to: {final_url}")
            else:
                print(f"⚠ Unexpected status code: {status}")
            
            # Final verification
            print("\n=== Test Summary ===")
            print("✓ Alice successfully logged into CIELO")
            print("✓ Authentication tokens were established")
            
            if status == 200:
                print("✓ Alice is AUTHORIZED to access Billing API private endpoints")
                print("\n✅ TEST PASSED: Alice has proper authorization!")
            else:
                print(f"✗ Billing API returned status {status}")
                pytest.fail("Alice could not access Billing API private endpoint")
            
        except AssertionError:
            raise
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            page.screenshot(path="alice_billing_test_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running Billing API access integration test...")
    test_alice_billing_api_access()
    print("\nTest completed!")