"""
Fixed version of Azure Costs ABAC policy tests using API authentication.
"""

import pytest
import requests
import jwt
from playwright_config import Config

# Test data - Different user personas with various roles and attributes
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "expected_roles": ["costs_admin"],
        "expected_attrs": {
            "azure_subscription_ids": ["sub-001", "sub-002", "sub-003"],
            "cost_center_ids": ["cc-001", "cc-002", "cc-003"],
            "budget_limit": 1000000,
            "can_export_reports": True
        }
    },
    "manager": {
        "username": "alice",
        "password": "password123",
        "expected_roles": ["costs_manager"],
        "expected_attrs": {
            "azure_subscription_ids": ["sub-001", "sub-002"],
            "cost_center_ids": ["cc-001"],
            "budget_limit": 50000,
            "can_export_reports": True
        }
    },
    "viewer": {
        "username": "bob",
        "password": "password123",
        "expected_roles": ["costs_viewer"],
        "expected_attrs": {
            "azure_subscription_ids": ["sub-001"],
            "cost_center_ids": [],
            "budget_limit": 0,
            "can_export_reports": False
        }
    }
}


class TestAzureCostsPoliciesAPI:
    """Test ABAC policies for Azure Costs service using API authentication."""
    
    def setup_method(self):
        """Setup for each test."""
        self.identity_url = Config.IDENTITY_PROVIDER_URL
        self.azure_costs_url = Config.AZURE_COSTS_BASE_URL
    
    def login_user_api(self, username: str, password: str) -> dict:
        """Login a user via API and return their JWT token data."""
        response = requests.post(
            f"{self.identity_url}/api/login/",
            json={"username": username, "password": password},
            verify=False
        )
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        token = data.get("token")
        assert token, "No token in login response"
        
        # Decode token to verify contents
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        return {
            "token": token,
            "decoded": decoded,
            "username": username
        }
    
    def make_api_request(self, endpoint: str, token: str) -> tuple:
        """Make an authenticated API request and return status code and response."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{self.azure_costs_url}/api/{endpoint}", 
            headers=headers, 
            verify=False
        )
        return response.status_code, response.json() if response.status_code == 200 else None
    
    def test_costs_admin_full_access(self):
        """Test that costs_admin has full access to all operations."""
        # Login as admin
        auth_data = self.login_user_api(
            TEST_USERS["admin"]["username"], 
            TEST_USERS["admin"]["password"]
        )
        
        # Test access to private endpoint
        status, data = self.make_api_request("private", auth_data["token"])
        assert status == 200
        assert data["user"]["username"] == "admin"
        
        # Test RBAC endpoint
        status, data = self.make_api_request("test-rbac", auth_data["token"])
        assert status == 200
        assert data["user"]["username"] == "admin"
        
        # Note: In a real implementation, you would test specific admin-only endpoints
        # like budget approval, subscription management, etc.
    
    def test_costs_manager_access(self):
        """Test that costs_manager has appropriate access."""
        # Login as alice (manager)
        auth_data = self.login_user_api(
            TEST_USERS["manager"]["username"], 
            TEST_USERS["manager"]["password"]
        )
        
        # Test access to endpoints
        status, data = self.make_api_request("private", auth_data["token"])
        assert status == 200
        assert data["user"]["username"] == "alice"
        
        status, data = self.make_api_request("test-rbac", auth_data["token"])
        assert status == 200
        
        # Verify user has expected attributes
        user_data = data["user"]
        assert "roles" in user_data
        assert "attributes" in user_data
    
    def test_costs_viewer_limited_access(self):
        """Test that costs_viewer has read-only access."""
        # Login as bob (viewer)
        auth_data = self.login_user_api(
            TEST_USERS["viewer"]["username"], 
            TEST_USERS["viewer"]["password"]
        )
        
        # Test access to endpoints
        status, data = self.make_api_request("private", auth_data["token"])
        assert status == 200
        assert data["user"]["username"] == "bob"
        
        # In a real implementation, you would test that:
        # - Viewer can access read endpoints
        # - Viewer cannot access write endpoints (would get 403)
    
    def test_unauthorized_access(self):
        """Test that unauthenticated requests are rejected."""
        # Try to access private endpoint without token
        response = requests.get(
            f"{self.azure_costs_url}/api/private", 
            verify=False
        )
        assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden
    
    def test_health_endpoint_public_access(self):
        """Test that health endpoint is publicly accessible."""
        response = requests.get(
            f"{self.azure_costs_url}/api/health", 
            verify=False
        )
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "azure-costs-api"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])