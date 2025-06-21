"""
Playwright test to verify user count display on Identity Admin roles page.
This test debugs and ensures the user count feature works correctly.
"""

import pytest
import pytest_asyncio
import json
import asyncio
import os
from playwright.async_api import async_playwright, Page, Response
from datetime import datetime

# Configure pytest to use asyncio
pytestmark = pytest.mark.asyncio

class TestRolesUserCount:
    """Test suite for verifying user count display on roles page."""
    
    # Test configuration - Always use Traefik endpoints as per project guidelines
    BASE_URL = "https://website.vfservices.viloforge.com"
    IDENTITY_PROVIDER_URL = "https://identity.vfservices.viloforge.com"
        
    TEST_USERNAME = "admin"
    TEST_PASSWORD = "admin123"  # From conftest.py
    
    # Storage for debugging
    api_responses = []
    console_messages = []
    network_errors = []
    
    @pytest_asyncio.fixture(autouse=True)
    async def setup_and_teardown(self):
        """Setup before each test and cleanup after."""
        self.api_responses = []
        self.console_messages = []
        self.network_errors = []
        yield
        # Print debugging info after test
        if self.api_responses:
            print("\n=== API Responses Captured ===")
            for resp in self.api_responses:
                print(f"\nURL: {resp['url']}")
                print(f"Status: {resp['status']}")
                print(f"Data: {json.dumps(resp['data'], indent=2)[:500]}...")
    
    async def login(self, page: Page):
        """Login to the identity admin interface."""
        print(f"\nLogging in as {self.TEST_USERNAME}...")
        
        # Navigate to login page
        await page.goto(f"{self.BASE_URL}/login/")
        await page.wait_for_load_state("networkidle")
        
        # Fill login form - try both username and email fields
        try:
            await page.fill('input[name="email"]', self.TEST_USERNAME)
        except:
            await page.fill('input[name="username"]', self.TEST_USERNAME)
        await page.fill('input[name="password"]', self.TEST_PASSWORD)
        
        # Submit form
        await page.click('button[type="submit"]')
        
        # Wait for redirect
        await page.wait_for_url("**/", timeout=10000)
        await page.wait_for_load_state("networkidle")
        print("Login successful")
    
    async def capture_api_response(self, response: Response):
        """Capture API responses for debugging."""
        if "/api/admin/roles" in response.url:
            try:
                data = await response.json()
                self.api_responses.append({
                    'url': response.url,
                    'status': response.status,
                    'data': data,
                    'headers': dict(response.headers)
                })
                print(f"\nCaptured API response from {response.url}")
                print(f"Status: {response.status}")
                print(f"Role count: {len(data) if isinstance(data, list) else 'N/A'}")
            except Exception as e:
                print(f"Error capturing response: {e}")
    
    async def capture_console_message(self, msg):
        """Capture console messages for debugging."""
        self.console_messages.append({
            'type': msg.type,
            'text': msg.text,
            'location': msg.location
        })
        if msg.type in ['error', 'warning']:
            print(f"\nConsole {msg.type}: {msg.text}")
    
    async def capture_network_error(self, request):
        """Capture failed network requests."""
        if request.failure:
            self.network_errors.append({
                'url': request.url,
                'failure': request.failure,
                'method': request.method
            })
            print(f"\nNetwork error: {request.method} {request.url} - {request.failure}")
    
    async def test_roles_page_user_count_display(self):
        """Test that roles page displays user count correctly."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set up event listeners for debugging
            page.on("response", self.capture_api_response)
            page.on("console", self.capture_console_message)
            page.on("requestfailed", self.capture_network_error)
            
            try:
                # Login
                await self.login(page)
                
                # Navigate to roles page
                print("\nNavigating to roles page...")
                await page.goto(f"{self.BASE_URL}/admin/roles/")
                
                # Wait for the page to load
                await page.wait_for_selector('#rolesTable', state='visible', timeout=15000)
                print("Roles table loaded")
                
                # Take screenshot for debugging
                await page.screenshot(path='roles_page_loaded.png')
                
                # Wait a bit for any async data loading
                await asyncio.sleep(2)
                
                # Check if roles are displayed
                role_rows = await page.query_selector_all('#rolesTable tbody tr')
                print(f"\nFound {len(role_rows)} role rows")
                
                # Verify user count is displayed for each role
                roles_without_count = []
                roles_with_count = []
                
                for i, row in enumerate(role_rows):
                    # Get role details
                    service = await row.query_selector('td:nth-child(1)')
                    service_text = await service.inner_text() if service else 'N/A'
                    
                    role_name = await row.query_selector('td:nth-child(2)')
                    role_text = await role_name.inner_text() if role_name else 'N/A'
                    
                    # Check user count column (5th column)
                    user_count_cell = await row.query_selector('td:nth-child(5)')
                    user_count_text = await user_count_cell.inner_text() if user_count_cell else 'N/A'
                    
                    # Check if user count badge exists
                    user_count_badge = await row.query_selector('td:nth-child(5) .badge')
                    has_badge = user_count_badge is not None
                    
                    print(f"\nRole {i+1}:")
                    print(f"  Service: {service_text}")
                    print(f"  Role: {role_text}")
                    print(f"  User Count Text: {user_count_text}")
                    print(f"  Has Badge: {has_badge}")
                    
                    if has_badge and 'user' in user_count_text.lower():
                        roles_with_count.append({
                            'service': service_text,
                            'role': role_text,
                            'count': user_count_text
                        })
                    else:
                        roles_without_count.append({
                            'service': service_text,
                            'role': role_text,
                            'displayed': user_count_text
                        })
                
                # Take screenshot of the table
                table_element = await page.query_selector('#rolesTable')
                if table_element:
                    await table_element.screenshot(path='roles_table_content.png')
                
                # Report results
                print(f"\n=== Test Results ===")
                print(f"Total roles: {len(role_rows)}")
                print(f"Roles with user count: {len(roles_with_count)}")
                print(f"Roles without user count: {len(roles_without_count)}")
                
                if roles_without_count:
                    print("\nRoles missing user count:")
                    for role in roles_without_count:
                        print(f"  - {role['service']}: {role['role']} (displayed: '{role['displayed']}')")
                
                # Assert that all roles have user count
                assert len(roles_without_count) == 0, f"{len(roles_without_count)} roles are missing user count display"
                
                # Additional checks
                assert len(role_rows) > 0, "No roles found in the table"
                assert len(self.network_errors) == 0, f"Network errors occurred: {self.network_errors}"
                
            except Exception as e:
                # Take screenshot on error
                await page.screenshot(path='error_screenshot.png', full_page=True)
                print(f"\nError occurred: {str(e)}")
                print(f"Screenshot saved as error_screenshot.png")
                raise
            
            finally:
                await browser.close()
    
    async def test_roles_api_response_structure(self):
        """Test the roles API response structure directly."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Set up response capture
            api_response_data = None
            
            async def capture_roles_api(response: Response):
                if "/api/admin/roles/" in response.url and response.status == 200:
                    nonlocal api_response_data
                    api_response_data = await response.json()
            
            page.on("response", capture_roles_api)
            
            try:
                # Login
                await self.login(page)
                
                # Navigate to roles page to trigger API call
                await page.goto(f"{self.BASE_URL}/roles/")
                await page.wait_for_selector('#rolesTable', timeout=15000)
                
                # Wait for API response
                await asyncio.sleep(3)
                
                # Verify API response
                assert api_response_data is not None, "No roles API response captured"
                
                print(f"\n=== API Response Analysis ===")
                print(f"Total roles in response: {len(api_response_data)}")
                
                # Check structure of first few roles
                for i, role in enumerate(api_response_data[:3]):
                    print(f"\nRole {i+1} structure:")
                    print(f"  Keys: {list(role.keys())}")
                    print(f"  Has user_count: {'user_count' in role}")
                    if 'user_count' in role:
                        print(f"  User count value: {role['user_count']}")
                
                # Verify all roles have user_count field
                roles_missing_count = [r for r in api_response_data if 'user_count' not in r]
                
                assert len(roles_missing_count) == 0, \
                    f"{len(roles_missing_count)} roles missing 'user_count' field in API response"
                
            finally:
                await browser.close()
    
    async def test_roles_page_performance(self):
        """Test roles page loading performance and check for JS errors."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Enable performance monitoring
            await context.tracing.start(screenshots=True, snapshots=True)
            
            js_errors = []
            page.on("console", lambda msg: js_errors.append(msg) if msg.type == "error" else None)
            
            try:
                # Login
                await self.login(page)
                
                # Measure page load time
                start_time = datetime.now()
                await page.goto(f"{self.BASE_URL}/roles/")
                await page.wait_for_selector('#rolesTable', state='visible', timeout=15000)
                load_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\nPage load time: {load_time:.2f} seconds")
                
                # Check for JavaScript errors
                if js_errors:
                    print(f"\nJavaScript errors found: {len(js_errors)}")
                    for error in js_errors:
                        print(f"  - {error.text}")
                
                # Check if DataTable initialized
                datatable_initialized = await page.evaluate("""
                    () => {
                        return typeof $ !== 'undefined' && 
                               $('#rolesTable').DataTable !== undefined &&
                               $.fn.dataTable.isDataTable('#rolesTable');
                    }
                """)
                
                print(f"DataTable initialized: {datatable_initialized}")
                
                # Check API configuration
                api_config = await page.evaluate("""
                    () => {
                        return {
                            useMockApi: window.USE_MOCK_API,
                            identityProviderUrl: window.IDENTITY_PROVIDER_URL,
                            hasApiClient: window.identityAdminClient !== undefined
                        };
                    }
                """)
                
                print(f"\nAPI Configuration:")
                print(f"  Using mock API: {api_config.get('useMockApi', 'Unknown')}")
                print(f"  Identity Provider URL: {api_config.get('identityProviderUrl', 'Unknown')}")
                print(f"  API Client initialized: {api_config.get('hasApiClient', False)}")
                
                # Assert no JS errors
                assert len(js_errors) == 0, f"JavaScript errors detected: {[e.text for e in js_errors]}"
                assert load_time < 10, f"Page took too long to load: {load_time:.2f} seconds"
                assert datatable_initialized, "DataTable not properly initialized"
                
            finally:
                await context.tracing.stop(path="trace.zip")
                await browser.close()
                print("\nPerformance trace saved as trace.zip")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s", "--tb=short"])