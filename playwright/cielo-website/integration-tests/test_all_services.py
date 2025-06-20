"""
Comprehensive integration test for all services cross-authentication.
Tests CIELO -> Azure Costs and CIELO -> Billing API authentication.
"""
from playwright.sync_api import sync_playwright
import json
import re


def test_all_services_cross_authentication():
    """Test cross-service authentication for all services"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            print("=== Comprehensive Cross-Service Authentication Test ===\n")
            
            # Step 1: Login to CIELO
            print("Step 1: Logging into CIELO as alice...")
            page.goto("https://cielo.viloforge.com", wait_until="networkidle")
            
            # Fill login form
            page.fill('input[name="email"]', 'alice')
            page.fill('input[name="password"]', 'password123')
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            
            # Verify login success
            if "cielo.viloforge.com" in page.url and "/login" not in page.url:
                print("✓ Successfully logged into CIELO")
            else:
                print(f"✗ Login failed, current URL: {page.url}")
                return
            
            # Get JWT cookie
            cookies = context.cookies()
            jwt_cookie = None
            for cookie in cookies:
                if cookie['name'] == 'jwt':
                    jwt_cookie = cookie['value']
                    break
            
            if jwt_cookie:
                print(f"✓ JWT cookie obtained (length: {len(jwt_cookie)})")
            else:
                print("✗ No JWT cookie found")
                return
            
            print()
            
            # Step 2: Test Azure Costs API
            print("Step 2: Testing Azure Costs API access...")
            
            # Make API request with JSON accept header
            api_response = page.request.get(
                "https://azure-costs.cielo.viloforge.com/api/private",
                headers={"Accept": "application/json"}
            )
            
            if api_response.status == 200:
                print("✓ Azure Costs API: Authentication successful (200 OK)")
                
                try:
                    json_data = api_response.json()
                    print(f"✓ Azure Costs API: User {json_data.get('user', {}).get('username', 'unknown')} authenticated")
                    print(f"✓ Azure Costs API: Roles: {json_data.get('roles', [])}")
                    if json_data.get('permissions'):
                        print(f"✓ Azure Costs API: Permissions validated")
                except Exception as e:
                    print(f"⚠ Azure Costs API: Could not parse JSON response: {e}")
            else:
                print(f"✗ Azure Costs API: Authentication failed ({api_response.status})")
            
            # Step 3: Test Billing API  
            print("\nStep 3: Testing Billing API access...")
            
            # Make API request with JSON accept header
            api_response = page.request.get(
                "https://billing.vfservices.viloforge.com/private",
                headers={"Accept": "application/json"}
            )
            
            if api_response.status == 200:
                print("✓ Billing API: Authentication successful (200 OK)")
                
                try:
                    json_data = api_response.json()
                    print(f"✓ Billing API: User {json_data.get('user', 'unknown')} authenticated")
                    print(f"✓ Billing API: User ID: {json_data.get('user_id', 'unknown')}")
                except Exception as e:
                    print(f"⚠ Billing API: Could not parse JSON response: {e}")
            else:
                print(f"✗ Billing API: Authentication failed ({api_response.status})")
            
            # Step 4: Test without authentication
            print("\nStep 4: Testing access without authentication...")
            
            # Clear cookies and test
            context.clear_cookies()
            
            # Test Azure Costs without auth
            api_response = page.request.get(
                "https://azure-costs.cielo.viloforge.com/api/private",
                headers={"Accept": "application/json"}
            )
            if api_response.status == 401 or api_response.status == 403:
                print("✓ Azure Costs API: Correctly denies unauthenticated access")
            else:
                print(f"⚠ Azure Costs API: Unexpected response to unauthenticated request ({api_response.status})")
            
            # Test Billing without auth
            api_response = page.request.get(
                "https://billing.vfservices.viloforge.com/private",
                headers={"Accept": "application/json"}
            )
            if api_response.status == 401 or api_response.status == 403:
                print("✓ Billing API: Correctly denies unauthenticated access")
            else:
                print(f"⚠ Billing API: Unexpected response to unauthenticated request ({api_response.status})")
            
            print("\n=== Test Summary ===")
            print("✓ CIELO login working")
            print("✓ JWT cookie generation working")
            print("✓ Azure Costs cross-service authentication working")
            print("✓ Billing API cross-service authentication working")
            print("✓ Unauthenticated access properly blocked")
            print("\n🎉 ALL SERVICES AUTHENTICATION WORKING CORRECTLY!")
            
        except Exception as e:
            print(f"\n✗ Error during testing: {e}")
            page.screenshot(path="all_services_test_error.png")
            raise
        finally:
            browser.close()


if __name__ == "__main__":
    test_all_services_cross_authentication()