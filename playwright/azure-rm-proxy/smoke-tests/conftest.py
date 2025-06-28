"""
Pytest configuration for Azure RM Proxy smoke tests.
"""
import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext
import os
import sys
import json
from typing import Generator, Dict
import httpx

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Configuration
ARM_PROXY_URL = "https://arm-proxy.maltacentral.com"
IDENTITY_PROVIDER_URL = "https://identity.vfservices.viloforge.com"
TEST_USER = {
    "email": "testuser@viloforge.com",
    "password": "testuser123!#QWERT"
}
ADMIN_USER = {
    "email": "admin@viloforge.com", 
    "password": "admin123!#QWERT"
}


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments."""
    return {
        "ignore_https_errors": True,
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture(scope="session")
def playwright_instance():
    """Create a Playwright instance."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance, browser_context_args):
    """Create a browser instance."""
    browser = playwright_instance.chromium.launch(
        headless=True,
        args=["--disable-dev-shm-usage", "--no-sandbox"]
    )
    yield browser
    browser.close()


@pytest.fixture
def context(browser, browser_context_args):
    """Create a new browser context for each test."""
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture
def page(context):
    """Create a new page for each test."""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def auth_token() -> str:
    """Get authentication token from identity provider."""
    response = httpx.post(
        f"{IDENTITY_PROVIDER_URL}/api/token/",
        json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"]
        },
        verify=False
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        pytest.skip(f"Failed to get auth token: {response.status_code}")


@pytest.fixture
def admin_auth_token() -> str:
    """Get admin authentication token from identity provider."""
    response = httpx.post(
        f"{IDENTITY_PROVIDER_URL}/api/token/",
        json={
            "email": ADMIN_USER["email"],
            "password": ADMIN_USER["password"]
        },
        verify=False
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        pytest.skip(f"Failed to get admin auth token: {response.status_code}")


@pytest.fixture
def api_headers(auth_token: str) -> Dict[str, str]:
    """Get headers for API requests with authentication."""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_api_headers(admin_auth_token: str) -> Dict[str, str]:
    """Get headers for admin API requests with authentication."""
    return {
        "Authorization": f"Bearer {admin_auth_token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }