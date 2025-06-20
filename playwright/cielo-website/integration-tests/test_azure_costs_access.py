"""
Integration test to verify alice can access Azure Costs API after logging in through CIELO.
Tests cross-service authentication between CIELO and Azure Costs.
"""
import pytest
from playwright.sync_api import sync_playwright, expect


def test_alice_azure_costs_api_access():
    """Test that alice can access Azure Costs API private endpoint after CIELO login"""
    with sync_playwright() as p:
        # Launch browser with debugging enabled
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        
        # Enable console logging for debugging
        page = context.new_page()
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        try:
            print("\n=== Testing Alice's Azure Costs API Access via CIELO ===")
            
            # Step 1: Login to CIELO as alice
            print("\nStep 1: Logging into CIELO as alice...")
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Should be redirected to login page
            assert "/accounts/login/" in page.url or "/login" in page.url
            print(f"✓ Redirected to login page: {page.url}")
            
            # Fill login form
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'password123')
            
            # Take screenshot of login form
            page.screenshot(path="alice_cielo_login.png")
            
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
            
            # Take screenshot of logged-in state
            page.screenshot(path="alice_cielo_logged_in.png")
            
            # Step 3: Access Azure Costs API private endpoint
            print("\nStep 3: Accessing Azure Costs API private endpoint...")
            
            # Navigate to Azure Costs API
            response = page.goto("https://azure-costs.cielo.viloforge.com/api/private", wait_until="networkidle")
            
            # Check response status
            status = response.status if response else None
            print(f"Response status: {status}")
            
            # Take screenshot of API response
            page.screenshot(path="alice_azure_costs_api_response.png")
            
            # Step 4: Verify authorization
            print("\nStep 4: Verifying authorization...")
            
            # Check if we got a successful response (200 OK)
            if status == 200:
                print("✓ Alice is authorized to access Azure Costs API private endpoint")
                
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
                    print("The JWT token from CIELO is not being passed to Azure Costs API")
                    print("This indicates a cross-domain authentication configuration issue")
                    print("\nPossible causes:")
                    print("1. JWT cookie domain is not set correctly for subdomain sharing")
                    print("2. Azure Costs API is not configured to accept CIELO's JWT tokens")
                    print("3. CORS or cookie policies preventing token sharing")
                    pytest.fail("Authentication tokens not shared between CIELO and Azure Costs")
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
            
            # Step 5: Test API functionality
            print("\nStep 5: Testing API functionality...")
            
            # Try to access another private endpoint
            response2 = page.goto("https://azure-costs.cielo.viloforge.com/api/private/health", wait_until="networkidle")
            status2 = response2.status if response2 else None
            
            if status2 == 200:
                print("✓ Can access private health endpoint")
            else:
                print(f"⚠ Private health endpoint returned status: {status2}")
            
            # Final verification
            print("\n=== Test Summary ===")
            print("✓ Alice successfully logged into CIELO")
            print("✓ Authentication tokens were established")
            
            if status == 200:
                print("✓ Alice is AUTHORIZED to access Azure Costs API private endpoints")
                print("\n✅ TEST PASSED: Alice has proper authorization!")
            else:
                print(f"✗ Azure Costs API returned status {status}")
                pytest.fail("Alice could not access Azure Costs API private endpoint")
            
        except AssertionError:
            raise
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
            page.screenshot(path="alice_test_error.png")
            raise
        finally:
            browser.close()


def test_alice_azure_costs_api_data_access():
    """Test that alice can retrieve actual data from Azure Costs API"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("\n=== Testing Alice's Azure Costs API Data Access ===")
            
            # Quick login
            print("\nLogging in as alice...")
            page.goto("https://cielo.viloforge.com/accounts/login/", wait_until="networkidle")
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            # Test various API endpoints
            api_endpoints = [
                ("https://azure-costs.cielo.viloforge.com/api/private", "Private API root"),
                ("https://azure-costs.cielo.viloforge.com/api/private/costs", "Costs data"),
                ("https://azure-costs.cielo.viloforge.com/api/private/subscriptions", "Subscriptions"),
                ("https://azure-costs.cielo.viloforge.com/api/private/budgets", "Budgets")
            ]
            
            print("\nTesting API endpoints:")
            successful_endpoints = 0
            
            for endpoint, description in api_endpoints:
                response = page.goto(endpoint, wait_until="networkidle")
                status = response.status if response else None
                
                if status == 200:
                    print(f"✓ {description}: Accessible (200 OK)")
                    successful_endpoints += 1
                elif status == 404:
                    print(f"⚠ {description}: Not Found (404) - endpoint may not exist")
                elif status == 401:
                    print(f"✗ {description}: Unauthorized (401)")
                elif status == 403:
                    print(f"✗ {description}: Forbidden (403)")
                else:
                    print(f"⚠ {description}: Status {status}")
            
            # Summary
            print(f"\n=== Summary ===")
            print(f"Accessible endpoints: {successful_endpoints}/{len(api_endpoints)}")
            
            if successful_endpoints > 0:
                print("✅ Alice has access to Azure Costs API data")
            else:
                pytest.fail("Alice cannot access any Azure Costs API endpoints")
            
        finally:
            browser.close()


if __name__ == "__main__":
    print("Running Azure Costs API access integration tests...")
    test_alice_azure_costs_api_access()
    test_alice_azure_costs_api_data_access()
    print("\nAll tests completed!")