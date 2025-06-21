"""
Pytest configuration for Identity Admin Playwright tests
"""
import pytest
import os
from playwright.sync_api import sync_playwright
import requests
import urllib3

# Disable SSL warnings for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Base URLs
IDENTITY_PROVIDER_URL = os.environ.get(
    'IDENTITY_PROVIDER_URL', 
    'https://identity.vfservices.viloforge.com'
)

# The host Django project URL where identity-admin is installed
# For testing, we'll use the website project
HOST_PROJECT_URL = os.environ.get(
    'HOST_PROJECT_URL',
    'https://vfservices.viloforge.com'
)


@pytest.fixture(scope="session")
def ensure_services_running():
    """Ensure required services are running before tests."""
    try:
        # Check Identity Provider
        response = requests.get(f"{IDENTITY_PROVIDER_URL}/api/status/", verify=False, timeout=5)
        assert response.status_code == 200, f"Identity Provider not responding at {IDENTITY_PROVIDER_URL}"
        
        # Check host project
        response = requests.get(f"{HOST_PROJECT_URL}/", verify=False, timeout=5)
        assert response.status_code in [200, 302], f"Host project not responding at {HOST_PROJECT_URL}"
        
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Services not available: {e}")


@pytest.fixture(scope="session")
def browser():
    """Create browser instance."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser):
    """Create browser context with necessary settings."""
    context = browser.new_context(
        ignore_https_errors=True,
        viewport={'width': 1280, 'height': 720}
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def admin_auth_cookies():
    """Get authentication cookies for admin user."""
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    response = requests.post(
        f"{IDENTITY_PROVIDER_URL}/api/login/",
        json=login_data,
        verify=False
    )
    
    if response.status_code == 200:
        token = response.json().get('token')
        return {
            'jwt': token,
            'jwt_token': token  # Some apps use different cookie names
        }
    else:
        pytest.fail(f"Failed to authenticate admin user: {response.text}")


@pytest.fixture
def authenticated_page(page, admin_auth_cookies):
    """Create a page with admin authentication."""
    # Set cookies for authentication
    for name, value in admin_auth_cookies.items():
        page.context.add_cookies([{
            'name': name,
            'value': value,
            'domain': '.viloforge.com',
            'path': '/'
        }])
    
    return page


def get_admin_token():
    """Helper function to get admin JWT token."""
    response = requests.post(
        f"{IDENTITY_PROVIDER_URL}/api/login/",
        json={"username": "admin", "password": "admin123"},
        verify=False
    )
    
    if response.status_code == 200:
        return response.json()['token']
    else:
        raise Exception(f"Failed to get admin token: {response.text}")