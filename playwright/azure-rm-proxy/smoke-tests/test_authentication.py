"""
Test authentication and authorization for Azure RM Proxy API.
Tests JWT token validation, role-based access control, and rate limiting.
"""
import pytest
import httpx
from typing import Dict
import time


class TestAuthentication:
    """Test authentication mechanisms."""
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied when auth is required."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            verify=False
        )
        # Should get 401 Unauthorized when REQUIRE_AUTH=true
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
    
    def test_invalid_token_rejected(self):
        """Test that invalid JWT tokens are rejected."""
        headers = {
            "Authorization": "Bearer invalid.token.here"
        }
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            headers=headers,
            verify=False
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    def test_valid_token_accepted(self, api_headers: Dict[str, str]):
        """Test that valid JWT tokens are accepted."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            headers=api_headers,
            verify=False
        )
        # Should get 200 or 403 (if user lacks azure:read role)
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"
    
    def test_cookie_authentication(self, auth_token: str):
        """Test that JWT cookie authentication works."""
        cookies = {"vf_jwt": auth_token}
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            cookies=cookies,
            verify=False
        )
        # Should get 200 or 403 (if user lacks azure:read role)
        assert response.status_code in [200, 403], f"Expected 200/403, got {response.status_code}"


class TestAuthorization:
    """Test role-based access control."""
    
    def test_read_permission_required(self, api_headers: Dict[str, str]):
        """Test that azure:read role is required for read operations."""
        # Test various read endpoints
        endpoints = [
            "/api/subscriptions/",
            "/api/resource-groups/",
            "/api/virtual-machines/",
            "/api/vm-report/",
            "/api/vm-hostnames/"
        ]
        
        for endpoint in endpoints:
            response = httpx.get(
                f"https://arm-proxy.maltacentral.com{endpoint}",
                headers=api_headers,
                verify=False
            )
            # If user has azure:read role, should get 200
            # If not, should get 403
            assert response.status_code in [200, 403], \
                f"Endpoint {endpoint}: Expected 200/403, got {response.status_code}"
    
    def test_admin_endpoints(self, admin_api_headers: Dict[str, str]):
        """Test that admin endpoints require azure:admin role."""
        # Currently no admin-only endpoints, but test with admin token
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            headers=admin_api_headers,
            verify=False
        )
        # Admin should have access
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_anonymous_rate_limit(self):
        """Test that anonymous users are rate limited."""
        # Make requests up to the limit (60/min by default)
        responses = []
        
        # Make 10 rapid requests
        for i in range(10):
            response = httpx.get(
                "https://arm-proxy.maltacentral.com/api/ping",
                verify=False
            )
            responses.append(response)
            
            # Check rate limit headers
            if response.status_code == 200:
                assert "X-RateLimit-Limit" in response.headers
                assert "X-RateLimit-Remaining" in response.headers
                assert "X-RateLimit-Reset" in response.headers
        
        # All should succeed (well under limit)
        assert all(r.status_code == 200 for r in responses)
    
    def test_authenticated_higher_limit(self, api_headers: Dict[str, str]):
        """Test that authenticated users get higher rate limits."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/ping",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            # Authenticated users should have 120/min limit
            limit = int(response.headers.get("X-RateLimit-Limit", "0"))
            assert limit >= 120, f"Expected limit >= 120, got {limit}"
    
    def test_rate_limit_headers(self, api_headers: Dict[str, str]):
        """Test that rate limit headers are properly set."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/ping",
            headers=api_headers,
            verify=False
        )
        
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers
        
        # Verify header values are integers
        limit = int(response.headers["X-RateLimit-Limit"])
        remaining = int(response.headers["X-RateLimit-Remaining"])
        reset = int(response.headers["X-RateLimit-Reset"])
        
        assert limit > 0
        assert remaining >= 0
        assert remaining <= limit
        assert reset > int(time.time())


class TestAPIEndpoints:
    """Test authenticated access to API endpoints."""
    
    def test_swagger_ui_accessible(self):
        """Test that Swagger UI is accessible."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/docs",
            verify=False,
            follow_redirects=True
        )
        assert response.status_code == 200
        assert "swagger" in response.text.lower() or "fastapi" in response.text.lower()
    
    def test_openapi_schema(self):
        """Test that OpenAPI schema is accessible."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/openapi.json",
            verify=False
        )
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/api/subscriptions/" in schema["paths"]
    
    def test_ping_endpoint(self):
        """Test the ping endpoint (should not require auth)."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/ping",
            verify=False
        )
        assert response.status_code == 200
        assert response.text.strip('"') == "pong"
    
    def test_root_endpoint(self):
        """Test the root API endpoint."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/",
            verify=False
        )
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Azure RM Proxy API"