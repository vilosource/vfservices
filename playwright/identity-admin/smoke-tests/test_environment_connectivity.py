#!/usr/bin/env python3
"""
Environment connectivity test for VFServices.
This test verifies that the test environment can reach the required endpoints.
"""

import pytest
import requests
import socket
import asyncio
from playwright.async_api import async_playwright

class TestEnvironmentConnectivity:
    """Test suite to verify environment connectivity."""
    
    ENDPOINTS = {
        "Website": "https://website.vfservices.viloforge.com",
        "Identity Provider": "https://identity.vfservices.viloforge.com",
        "Admin Portal": "https://website.vfservices.viloforge.com/admin"
    }
    
    def test_dns_resolution(self):
        """Test DNS resolution for all endpoints."""
        print("\n=== DNS Resolution Test ===")
        
        for name, url in self.ENDPOINTS.items():
            hostname = url.replace("https://", "").split("/")[0]
            try:
                ip = socket.gethostbyname(hostname)
                print(f"✓ {name} ({hostname}): {ip}")
            except socket.gaierror as e:
                print(f"✗ {name} ({hostname}): DNS resolution failed - {e}")
                pytest.fail(f"Cannot resolve {hostname}")
    
    def test_http_connectivity(self):
        """Test HTTP connectivity to endpoints."""
        print("\n=== HTTP Connectivity Test ===")
        
        for name, url in self.ENDPOINTS.items():
            try:
                response = requests.get(url, timeout=5, verify=True)
                print(f"✓ {name}: HTTP {response.status_code}")
            except requests.exceptions.SSLError as e:
                print(f"⚠ {name}: SSL Error - {str(e)[:100]}...")
            except requests.exceptions.ConnectionError as e:
                print(f"✗ {name}: Connection Error - {str(e)[:100]}...")
                pytest.fail(f"Cannot connect to {url}")
            except requests.exceptions.Timeout:
                print(f"✗ {name}: Timeout after 5 seconds")
                pytest.fail(f"Timeout connecting to {url}")
    
    @pytest.mark.asyncio
    async def test_playwright_connectivity(self):
        """Test Playwright browser connectivity."""
        print("\n=== Playwright Browser Test ===")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                ignore_https_errors=False,  # Don't ignore SSL errors
                accept_downloads=False
            )
            page = await context.new_page()
            
            for name, url in self.ENDPOINTS.items():
                try:
                    response = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    print(f"✓ {name}: Status {response.status if response else 'N/A'}")
                except Exception as e:
                    print(f"✗ {name}: {type(e).__name__} - {str(e)[:100]}...")
                    # Don't fail here, just report
            
            await browser.close()
    
    def test_identity_provider_api(self):
        """Test Identity Provider API accessibility."""
        print("\n=== Identity Provider API Test ===")
        
        api_endpoints = [
            "/api/schema/",
            "/api/admin/roles/",
            "/api/admin/services/"
        ]
        
        base_url = "https://identity.vfservices.viloforge.com"
        
        for endpoint in api_endpoints:
            url = base_url + endpoint
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 401:
                    print(f"✓ {endpoint}: HTTP 401 (Authentication required - expected)")
                elif response.status_code == 200:
                    print(f"✓ {endpoint}: HTTP 200 (Public endpoint)")
                else:
                    print(f"⚠ {endpoint}: HTTP {response.status_code}")
            except Exception as e:
                print(f"✗ {endpoint}: {type(e).__name__} - {str(e)[:50]}...")


if __name__ == "__main__":
    # Run the tests
    import subprocess
    import sys
    
    print("Running VFServices Environment Connectivity Tests")
    print("=" * 50)
    
    # Run pytest with verbose output
    result = subprocess.run(
        [sys.executable, "-m", "pytest", __file__, "-v", "-s"],
        capture_output=False
    )
    
    sys.exit(result.returncode)