"""
Smoke tests for Azure Costs API endpoints using Playwright.
Tests the health, private, and RBAC endpoints through Traefik.
"""
import os
import pytest
from playwright.sync_api import Page, expect
import requests
from urllib.parse import urljoin
from playwright_config import Config


# Base URL for the Azure Costs service through Traefik
BASE_URL = Config.AZURE_COSTS_BASE_URL
IDENTITY_PROVIDER_URL = Config.IDENTITY_PROVIDER_URL

# Test credentials
TEST_USERNAME = Config.TEST_USERNAME
TEST_PASSWORD = Config.TEST_PASSWORD


class TestAzureCostsAPI:
    """Test suite for Azure Costs API endpoints."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data."""
        self.jwt_token = None
    
    def get_jwt_token(self):
        """Get JWT token from identity provider."""
        if self.jwt_token:
            return self.jwt_token
            
        # Login to get JWT token
        login_url = urljoin(IDENTITY_PROVIDER_URL, "/api/login/")
        print(f"Attempting login at: {login_url}")
        print(f"Username: {TEST_USERNAME}")
        response = requests.post(
            login_url,
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            verify=False  # For local testing with self-signed certs
        )
        
        if response.status_code == 200:
            data = response.json()
            self.jwt_token = data.get("token") or data.get("access_token")
            if self.jwt_token:
                return self.jwt_token
            else:
                pytest.skip("No token found in response")
        else:
            pytest.skip(f"Failed to get JWT token: {response.status_code} - {response.text}")
    
    def test_health_endpoint(self, page: Page):
        """Test the public health endpoint."""
        # Navigate to health endpoint
        response = page.request.get(f"{BASE_URL}/api/health")
        
        # Check response status
        assert response.status == 200, f"Expected 200, got {response.status}"
        
        # Check response content
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "azure-costs-api"
        assert "timestamp" in data
        assert "version" in data
        
        print("✓ Health endpoint test passed")
    
    def test_private_endpoint_without_auth(self, page: Page):
        """Test the private endpoint without authentication (should fail)."""
        # Try to access private endpoint without auth
        response = page.request.get(f"{BASE_URL}/api/private")
        
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status in [401, 403], f"Expected 401/403, got {response.status}"
        
        print("✓ Private endpoint correctly requires authentication")
    
    def test_private_endpoint_with_auth(self, page: Page):
        """Test the private endpoint with authentication."""
        # Get JWT token
        token = self.get_jwt_token()
        if not token:
            pytest.skip("No JWT token available")
        
        # Access private endpoint with auth
        response = page.request.get(
            f"{BASE_URL}/api/private",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Check response status
        assert response.status == 200, f"Expected 200, got {response.status}"
        
        # Check response content
        data = response.json()
        assert data["message"] == "This is a private endpoint"
        assert "user" in data
        assert "timestamp" in data
        
        # Verify user data
        user = data["user"]
        assert "id" in user
        assert "username" in user
        
        print("✓ Private endpoint with auth test passed")
    
    def test_rbac_endpoint_without_auth(self, page: Page):
        """Test the RBAC endpoint without authentication (should fail)."""
        # Try to access RBAC endpoint without auth
        response = page.request.get(f"{BASE_URL}/api/test-rbac")
        
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status in [401, 403], f"Expected 401/403, got {response.status}"
        
        print("✓ RBAC endpoint correctly requires authentication")
    
    def test_rbac_endpoint_with_auth(self, page: Page):
        """Test the RBAC endpoint with authentication."""
        # Get JWT token
        token = self.get_jwt_token()
        if not token:
            pytest.skip("No JWT token available")
        
        # Access RBAC endpoint with auth
        response = page.request.get(
            f"{BASE_URL}/api/test-rbac",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Check response status
        assert response.status == 200, f"Expected 200, got {response.status}"
        
        # Check response content
        data = response.json()
        assert data["message"] == "RBAC test successful"
        assert "user" in data
        assert "has_access" in data
        assert "timestamp" in data
        
        # Verify user object structure
        user = data["user"]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "roles" in user
        assert "attributes" in user
        
        # Verify data types
        assert isinstance(user["roles"], list)
        assert isinstance(user["attributes"], dict)
        assert isinstance(data["has_access"], bool)
        
        print("✓ RBAC endpoint with auth test passed")
    
    def test_cors_headers(self, page: Page):
        """Test CORS headers on the API endpoints."""
        # Test CORS on health endpoint
        response = page.request.get(
            f"{BASE_URL}/api/health",
            headers={"Origin": "https://cielo.viloforge.com"}
        )
        
        # Check CORS headers
        headers = response.headers
        assert "access-control-allow-origin" in headers or "Access-Control-Allow-Origin" in headers
        
        print("✓ CORS headers test passed")
    
    def test_invalid_endpoint(self, page: Page):
        """Test that invalid endpoints return 404."""
        # Try to access non-existent endpoint
        response = page.request.get(f"{BASE_URL}/api/nonexistent")
        
        # Should return 404 Not Found
        assert response.status == 404, f"Expected 404, got {response.status}"
        
        print("✓ Invalid endpoint test passed")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])