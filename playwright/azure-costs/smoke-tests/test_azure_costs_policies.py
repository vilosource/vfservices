"""
Smoke tests for Azure Costs ABAC policies.

This test verifies that the ABAC policies are correctly enforced for different
user roles and attributes when accessing the Azure Costs service.
"""

import os
import sys
import pytest
from playwright.sync_api import Page, expect
import jwt
import time
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from playwright.common.auth import authenticated_page, AuthenticationError


# Test data - Different user personas with various roles and attributes
TEST_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "expected_roles": ["costs_admin"],
        "expected_attrs": {
            "azure_subscription_ids": ["sub-001", "sub-002", "sub-003"],
            "cost_center_ids": ["cc-001", "cc-002"],
            "budget_limit": 1000000,
            "can_export_reports": True
        }
    },
    "manager": {
        "username": "alice",  # Alice has costs_manager role in the demo setup
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
        "username": "bob",  # Bob has costs_viewer role in the demo setup
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


class TestAzureCostsPolicies:
    """Test ABAC policies for Azure Costs service."""
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Setup for each test."""
        self.page = page
        self.base_url = "https://cielo.viloforge.com"
        self.identity_url = "https://identity.cielo.viloforge.com"
        self.azure_costs_url = "https://azure-costs.cielo.viloforge.com"
    
    def login_user(self, username: str, password: str) -> dict:
        """Login a user and return their JWT token data."""
        # Use the authentication utility
        with authenticated_page(self.page, username, password, 
                              base_url=self.identity_url) as auth_page:
            # Navigate to profile page to ensure login completed
            auth_page.goto(f"{self.identity_url}/profile/", wait_until="networkidle")
            
            # Get JWT token
            jwt_token = auth_page.get_jwt_token()
            assert jwt_token, "JWT token not found after login"
            
            # Decode token to verify contents
            decoded = jwt.decode(jwt_token, options={"verify_signature": False})
            
            return {
                "token": jwt_token,
                "decoded": decoded,
                "username": username
            }
    
    def make_api_request(self, endpoint: str, token: str) -> tuple:
        """Make an authenticated API request and return status code and response."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{self.azure_costs_url}/api/{endpoint}", headers=headers, verify=False)
        return response.status_code, response.json() if response.status_code == 200 else None
    
    def test_costs_admin_full_access(self):
        """Test that costs_admin has full access to all operations."""
        # Login as admin
        auth_data = self.login_user(TEST_USERS["admin"]["username"], TEST_USERS["admin"]["password"])
        
        # Verify roles and attributes in JWT
        assert "costs_admin" in auth_data["decoded"]["roles"]
        assert auth_data["decoded"]["attributes"]["budget_limit"] == 1000000
        assert auth_data["decoded"]["attributes"]["can_export_reports"] is True
        
        # Test API access
        status, data = self.make_api_request("test-rbac", auth_data["token"])
        assert status == 200
        assert data["has_access"] is True
        assert "costs_admin" in data["roles"]
    
    def test_costs_manager_limited_access(self):
        """Test that costs_manager has limited access based on attributes."""
        # Login as manager (alice)
        auth_data = self.login_user(TEST_USERS["manager"]["username"], TEST_USERS["manager"]["password"])
        
        # Verify roles and attributes
        assert "costs_manager" in auth_data["decoded"]["roles"]
        assert auth_data["decoded"]["attributes"]["budget_limit"] == 50000
        assert len(auth_data["decoded"]["attributes"]["azure_subscription_ids"]) == 2
        
        # Test API access
        status, data = self.make_api_request("test-rbac", auth_data["token"])
        assert status == 200
        assert data["has_access"] is True
        assert "costs_manager" in data["roles"]
    
    def test_costs_viewer_read_only_access(self):
        """Test that costs_viewer has read-only access."""
        # Login as viewer (bob)
        auth_data = self.login_user(TEST_USERS["viewer"]["username"], TEST_USERS["viewer"]["password"])
        
        # Verify roles and attributes
        assert "costs_viewer" in auth_data["decoded"]["roles"]
        assert auth_data["decoded"]["attributes"]["budget_limit"] == 0
        assert auth_data["decoded"]["attributes"]["can_export_reports"] is False
        
        # Test API access
        status, data = self.make_api_request("test-rbac", auth_data["token"])
        assert status == 200
        assert data["has_access"] is True
        assert "costs_viewer" in data["roles"]
    
    def test_subscription_based_access(self):
        """Test that users can only access their assigned subscriptions."""
        # Login as viewer with limited subscription access
        auth_data = self.login_user(TEST_USERS["viewer"]["username"], TEST_USERS["viewer"]["password"])
        
        # Verify they only have access to sub-001
        attrs = auth_data["decoded"]["attributes"]
        assert "sub-001" in attrs["azure_subscription_ids"]
        assert "sub-002" not in attrs["azure_subscription_ids"]
        assert "sub-003" not in attrs["azure_subscription_ids"]
    
    def test_budget_limit_enforcement(self):
        """Test that budget limits are properly set for different roles."""
        for user_type, user_data in TEST_USERS.items():
            auth_data = self.login_user(user_data["username"], user_data["password"])
            
            # Verify budget limit
            actual_limit = auth_data["decoded"]["attributes"]["budget_limit"]
            expected_limit = user_data["expected_attrs"]["budget_limit"]
            assert actual_limit == expected_limit, f"{user_type} should have budget limit of {expected_limit}"
    
    def test_export_permission(self):
        """Test that export permissions are correctly assigned."""
        # Admin and manager should have export permission
        for user_type in ["admin", "manager"]:
            auth_data = self.login_user(TEST_USERS[user_type]["username"], TEST_USERS[user_type]["password"])
            assert auth_data["decoded"]["attributes"]["can_export_reports"] is True
        
        # Viewer should not have export permission
        auth_data = self.login_user(TEST_USERS["viewer"]["username"], TEST_USERS["viewer"]["password"])
        assert auth_data["decoded"]["attributes"]["can_export_reports"] is False
    
    def test_cost_center_access(self):
        """Test cost center based access control."""
        # Manager should have access to cc-001
        auth_data = self.login_user(TEST_USERS["manager"]["username"], TEST_USERS["manager"]["password"])
        assert "cc-001" in auth_data["decoded"]["attributes"]["cost_center_ids"]
        
        # Viewer should not have access to any cost centers
        auth_data = self.login_user(TEST_USERS["viewer"]["username"], TEST_USERS["viewer"]["password"])
        assert len(auth_data["decoded"]["attributes"]["cost_center_ids"]) == 0
    
    def test_unauthorized_access(self):
        """Test that unauthenticated requests are rejected."""
        # Try to access private endpoint without token
        response = requests.get(f"{self.azure_costs_url}/api/private", verify=False)
        assert response.status_code == 401
    
    def test_health_endpoint_public_access(self):
        """Test that health endpoint is publicly accessible."""
        response = requests.get(f"{self.azure_costs_url}/api/health", verify=False)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "azure-costs-api"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])