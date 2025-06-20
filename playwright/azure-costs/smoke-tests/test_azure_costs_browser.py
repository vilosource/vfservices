"""
Browser-based smoke tests for Azure Costs API using Playwright.
These tests simulate browser interactions with the API endpoints.
"""
import os
import json
import pytest
from playwright.sync_api import Page, expect, BrowserContext
from urllib.parse import urljoin


# Base URLs
BASE_URL = os.environ.get("AZURE_COSTS_BASE_URL", "https://azure-costs.cielo.viloforge.com")
IDENTITY_PROVIDER_URL = os.environ.get("IDENTITY_PROVIDER_URL", "https://identity.cielo.viloforge.com")
CIELO_WEBSITE_URL = os.environ.get("CIELO_WEBSITE_URL", "https://cielo.viloforge.com")

# Test credentials
TEST_USERNAME = os.environ.get("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "testpass123")


class TestAzureCostsBrowser:
    """Browser-based test suite for Azure Costs API."""
    
    def login_and_get_token(self, page: Page, context: BrowserContext) -> str:
        """Login through the identity provider and get JWT token."""
        # Navigate to login page
        page.goto(f"{IDENTITY_PROVIDER_URL}/login/", wait_until="networkidle")
        
        # Fill login form
        page.fill('input[name="username"]', TEST_USERNAME)
        page.fill('input[name="password"]', TEST_PASSWORD)
        
        # Submit form
        page.click('button[type="submit"]')
        
        # Wait for redirect or login success
        page.wait_for_load_state("networkidle")
        
        # Get JWT token from cookies or local storage
        cookies = context.cookies()
        for cookie in cookies:
            if cookie["name"] == "jwt_token":
                return cookie["value"]
        
        # Check local storage
        token = page.evaluate("() => localStorage.getItem('jwt_token')")
        if token:
            return token
            
        # If no token found, skip test
        pytest.skip("Could not obtain JWT token after login")
    
    def test_api_health_in_browser(self, page: Page):
        """Test accessing the health endpoint directly in browser."""
        # Navigate to health endpoint
        page.goto(f"{BASE_URL}/api/health", wait_until="networkidle")
        
        # Check that JSON is displayed
        content = page.content()
        
        # Parse the JSON response shown in browser
        # Most browsers will display JSON in a pre tag or as plain text
        json_text = page.locator("pre").text_content() or page.locator("body").text_content()
        
        try:
            data = json.loads(json_text)
            assert data["status"] == "healthy"
            assert data["service"] == "azure-costs-api"
            print("✓ Browser health endpoint test passed")
        except json.JSONDecodeError:
            pytest.fail("Could not parse JSON response in browser")
    
    def test_api_integration_with_cielo_website(self, page: Page, context: BrowserContext):
        """Test Azure Costs API integration with CIELO website."""
        # First, login to get authentication
        token = self.login_and_get_token(page, context)
        
        # Navigate to CIELO website
        page.goto(CIELO_WEBSITE_URL, wait_until="networkidle")
        
        # Check if there's any Azure Costs integration on the dashboard
        # This assumes the CIELO website might have links or calls to Azure Costs API
        
        # Set authorization header for API calls
        page.set_extra_http_headers({"Authorization": f"Bearer {token}"})
        
        # Listen for API calls to Azure Costs
        api_calls = []
        
        def handle_request(request):
            if BASE_URL in request.url:
                api_calls.append(request.url)
        
        page.on("request", handle_request)
        
        # Navigate to a page that might use Azure Costs API
        # For now, we'll just verify the API is accessible
        response = page.request.get(f"{BASE_URL}/api/private")
        assert response.status == 200
        
        print("✓ API integration test passed")
    
    def test_api_error_handling(self, page: Page):
        """Test API error handling and responses."""
        # Test with invalid JWT token
        page.set_extra_http_headers({"Authorization": "Bearer invalid_token"})
        
        response = page.request.get(f"{BASE_URL}/api/private")
        assert response.status in [401, 403]
        
        # Test with malformed authorization header
        page.set_extra_http_headers({"Authorization": "InvalidFormat"})
        
        response = page.request.get(f"{BASE_URL}/api/test-rbac")
        assert response.status in [401, 403]
        
        print("✓ API error handling test passed")
    
    def test_api_performance(self, page: Page):
        """Test API response times."""
        import time
        
        # Measure health endpoint response time
        start_time = time.time()
        response = page.request.get(f"{BASE_URL}/api/health")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Health endpoint should respond quickly (under 1 second)
        assert response_time < 1.0, f"Health endpoint took {response_time:.2f}s"
        assert response.status == 200
        
        print(f"✓ API performance test passed (response time: {response_time:.2f}s)")
    
    @pytest.mark.parametrize("endpoint,method", [
        ("/api/health", "GET"),
        ("/api/health", "POST"),
        ("/api/health", "PUT"),
        ("/api/health", "DELETE"),
        ("/api/private", "POST"),
        ("/api/test-rbac", "POST"),
    ])
    def test_http_methods(self, page: Page, endpoint: str, method: str):
        """Test that endpoints only accept appropriate HTTP methods."""
        url = f"{BASE_URL}{endpoint}"
        
        if method == "GET":
            response = page.request.get(url)
        elif method == "POST":
            response = page.request.post(url, data={})
        elif method == "PUT":
            response = page.request.put(url, data={})
        elif method == "DELETE":
            response = page.request.delete(url)
        
        # Health endpoint should only accept GET
        if endpoint == "/api/health":
            if method == "GET":
                assert response.status == 200
            else:
                assert response.status in [405, 404]  # Method Not Allowed or Not Found
        
        # Other endpoints should only accept GET
        elif endpoint in ["/api/private", "/api/test-rbac"]:
            if method == "GET":
                assert response.status in [401, 403]  # Requires auth
            else:
                assert response.status in [405, 404, 403]  # Method Not Allowed, Not Found, or Forbidden
        
        print(f"✓ HTTP method test passed for {method} {endpoint}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])