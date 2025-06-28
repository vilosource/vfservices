"""
Test Azure RM Proxy API endpoints functionality.
Tests all API endpoints with proper authentication.
"""
import pytest
import httpx
from typing import Dict, List


class TestSubscriptionsAPI:
    """Test subscriptions endpoints."""
    
    def test_list_subscriptions(self, api_headers: Dict[str, str]):
        """Test listing Azure subscriptions."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            # Successfully retrieved subscriptions
            data = response.json()
            assert isinstance(data, list)
            
            # Check subscription structure if any exist
            if data:
                subscription = data[0]
                assert "id" in subscription
                assert "displayName" in subscription
                assert "state" in subscription
        elif response.status_code == 403:
            # User lacks azure:read permission
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_list_subscriptions_with_refresh(self, api_headers: Dict[str, str]):
        """Test listing subscriptions with cache refresh."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/?refresh=true",
            headers=api_headers,
            verify=False
        )
        
        assert response.status_code in [200, 403]


class TestResourceGroupsAPI:
    """Test resource groups endpoints."""
    
    def test_list_resource_groups(self, api_headers: Dict[str, str]):
        """Test listing resource groups."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/resource-groups/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Check resource group structure if any exist
            if data:
                rg = data[0]
                assert "id" in rg
                assert "name" in rg
                assert "location" in rg
                assert "tags" in rg
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestVirtualMachinesAPI:
    """Test virtual machines endpoints."""
    
    def test_list_virtual_machines(self, api_headers: Dict[str, str]):
        """Test listing virtual machines."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/virtual-machines/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            
            # Check VM structure if any exist
            if data:
                vm = data[0]
                assert "id" in vm
                assert "name" in vm
                assert "location" in vm
                assert "properties" in vm
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_list_vms_with_details(self, api_headers: Dict[str, str]):
        """Test listing VMs with detailed information."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/virtual-machines/?include_details=true",
            headers=api_headers,
            verify=False
        )
        
        assert response.status_code in [200, 403]
    
    def test_vm_shortcuts(self, api_headers: Dict[str, str]):
        """Test VM shortcuts endpoint."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/vm/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestReportsAPI:
    """Test report endpoints."""
    
    def test_vm_report(self, api_headers: Dict[str, str]):
        """Test VM report generation."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/vm-report/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
            assert "report_date" in data
            assert "virtual_machines" in data
            assert isinstance(data["virtual_machines"], list)
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_vm_hostnames(self, api_headers: Dict[str, str]):
        """Test VM hostnames listing."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/vm-hostnames/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestNetworkingAPI:
    """Test networking-related endpoints."""
    
    def test_list_virtual_networks(self, api_headers: Dict[str, str]):
        """Test listing virtual networks."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/virtual-networks/",
            headers=api_headers,
            verify=False
        )
        
        # This endpoint might not exist in all deployments
        if response.status_code == 404:
            pytest.skip("Virtual networks endpoint not available")
        elif response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_list_route_tables(self, api_headers: Dict[str, str]):
        """Test listing route tables."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/routes/",
            headers=api_headers,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
        elif response.status_code == 403:
            assert "Permission denied" in response.text
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")


class TestErrorHandling:
    """Test API error handling."""
    
    def test_404_for_nonexistent_endpoint(self, api_headers: Dict[str, str]):
        """Test that nonexistent endpoints return 404."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/nonexistent/",
            headers=api_headers,
            verify=False
        )
        assert response.status_code == 404
    
    def test_invalid_query_parameters(self, api_headers: Dict[str, str]):
        """Test handling of invalid query parameters."""
        response = httpx.get(
            "https://arm-proxy.maltacentral.com/api/subscriptions/?invalid_param=true",
            headers=api_headers,
            verify=False
        )
        # Should still work, just ignore invalid params
        assert response.status_code in [200, 403]
    
    def test_method_not_allowed(self, api_headers: Dict[str, str]):
        """Test that unsupported HTTP methods return 405."""
        response = httpx.post(
            "https://arm-proxy.maltacentral.com/api/subscriptions/",
            headers=api_headers,
            verify=False
        )
        assert response.status_code == 405