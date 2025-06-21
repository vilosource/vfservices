"""
Pytest configuration for Identity Provider Playwright tests
"""
import pytest
from playwright.sync_api import sync_playwright
import requests
import time
from urllib.parse import urljoin
import json
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Base URLs for services accessed through Traefik domains
IDENTITY_PROVIDER_URL = "https://identity.vfservices.viloforge.com"


@pytest.fixture(scope="session")
def browser():
    """Create a browser instance for the test session"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage']
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new page for each test"""
    context = browser.new_context(
        viewport={'width': 1280, 'height': 720},
        ignore_https_errors=True
    )
    page = context.new_page()
    yield page
    context.close()


@pytest.fixture(scope="function")
def admin_auth_cookies():
    """Get authentication cookies for admin user"""
    # Login as admin user
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    # Use the API login endpoint
    response = requests.post(
        urljoin(IDENTITY_PROVIDER_URL, "api/login/"),
        json=login_data,
        allow_redirects=False,
        verify=False  # For self-signed certificates
    )
    
    if response.status_code != 200:
        # If admin user doesn't exist, try superuser
        login_data = {
            "username": "superuser",
            "password": "superpass123"
        }
        response = requests.post(
            urljoin(IDENTITY_PROVIDER_URL, "api/login/"),
            json=login_data,
            allow_redirects=False,
            verify=False  # For self-signed certificates
        )
    
    if response.status_code == 200:
        # API returns token in response body
        token = response.json().get('token')
        if token:
            # Return as cookie format for consistency
            return {'jwt': token}
        else:
            raise Exception("No token in response")
    
    raise Exception(f"Failed to authenticate admin user: {response.status_code}")


@pytest.fixture(scope="function")
def regular_auth_cookies():
    """Get authentication cookies for regular user"""
    # Login as regular user
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    
    response = requests.post(
        urljoin(IDENTITY_PROVIDER_URL, "api/login/"),
        json=login_data,
        allow_redirects=False,
        verify=False  # For self-signed certificates
    )
    
    if response.status_code == 200:
        # API returns token in response body
        token = response.json().get('token')
        if token:
            # Return as cookie format for consistency
            return {'jwt': token}
    
    # User might not exist, return empty cookies
    return {}


@pytest.fixture(scope="function")
def api_client(page):
    """Create an API client helper for the page"""
    class APIClient:
        def __init__(self, page):
            self.page = page
            self.base_url = IDENTITY_PROVIDER_URL
        
        def request(self, method, endpoint, data=None, headers=None):
            """Make an API request using page.evaluate"""
            url = urljoin(self.base_url, endpoint)
            
            # Build fetch options
            options = {
                'method': method,
                'headers': headers or {},
                'credentials': 'include'
            }
            
            if data:
                options['body'] = json.dumps(data)
                options['headers']['Content-Type'] = 'application/json'
            
            # Execute request in browser context
            response = self.page.evaluate(f"""
                (async () => {{
                    const url = '{url}';
                    const options = {json.dumps(options)};
                    const response = await fetch(url, options);
                    const data = await response.text();
                    let jsonData = null;
                    try {{
                        jsonData = JSON.parse(data);
                    }} catch (e) {{
                        // Not JSON
                    }}
                    return {{
                        status: response.status,
                        statusText: response.statusText,
                        headers: Object.fromEntries(response.headers.entries()),
                        data: data,
                        json: jsonData
                    }};
                }})()
            """)
            
            return response
        
        def get(self, endpoint, headers=None):
            return self.request('GET', endpoint, headers=headers)
        
        def post(self, endpoint, data=None, headers=None):
            return self.request('POST', endpoint, data, headers)
        
        def patch(self, endpoint, data=None, headers=None):
            return self.request('PATCH', endpoint, data, headers)
        
        def delete(self, endpoint, headers=None):
            return self.request('DELETE', endpoint, headers=headers)
    
    return APIClient(page)


def wait_for_service(url, timeout=30):
    """Wait for a service to be available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5, verify=False)
            if response.status_code < 500:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(1)
    return False


@pytest.fixture(scope="session", autouse=True)
def ensure_services_running():
    """Ensure all required services are running"""
    services = [
        (IDENTITY_PROVIDER_URL, "Identity Provider"),
    ]
    
    for url, name in services:
        if not wait_for_service(url):
            pytest.exit(f"{name} service is not available at {url}")