"""
Pytest configuration and fixtures for Azure Costs API Playwright tests.
"""
import os
import pytest
from typing import Generator
from playwright.sync_api import Playwright, Browser, BrowserContext, Page
from playwright_config import Config


@pytest.fixture(scope="session")
def browser_context_args():
    """Browser context arguments."""
    return {
        "ignore_https_errors": Config.IGNORE_HTTPS_ERRORS,
        "viewport": {"width": 1280, "height": 720},
        "record_video_dir": Config.VIDEO_DIR if Config.RECORD_VIDEO else None,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Browser launch arguments."""
    return {
        "headless": Config.HEADLESS,
        "slow_mo": Config.SLOW_MO,
    }


@pytest.fixture(scope="session")
def playwright() -> Generator[Playwright, None, None]:
    """Playwright instance."""
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright: Playwright, browser_type_launch_args) -> Generator[Browser, None, None]:
    """Browser instance."""
    browser = playwright.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser, browser_context_args) -> Generator[BrowserContext, None, None]:
    """Browser context for each test."""
    context = browser.new_context(**browser_context_args)
    context.set_default_timeout(Config.DEFAULT_TIMEOUT)
    context.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Page instance for each test."""
    page = context.new_page()
    yield page
    
    # Take screenshot on failure if configured
    if Config.SCREENSHOT_ON_FAILURE and hasattr(pytest, "_test_failed"):
        os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
        test_name = pytest._test_failed.get("name", "unknown")
        screenshot_path = os.path.join(Config.SCREENSHOT_DIR, f"{test_name}.png")
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved: {screenshot_path}")
    
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page, context: BrowserContext) -> Page:
    """Page with authentication already set up."""
    # This fixture would handle the login process and return a page with auth
    # For now, it's a placeholder that returns the regular page
    # In a real implementation, this would:
    # 1. Navigate to identity provider
    # 2. Perform login
    # 3. Get JWT token
    # 4. Set authorization headers
    return page


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment before running tests."""
    # Create directories for screenshots and videos if needed
    if Config.SCREENSHOT_ON_FAILURE:
        os.makedirs(Config.SCREENSHOT_DIR, exist_ok=True)
    if Config.RECORD_VIDEO:
        os.makedirs(Config.VIDEO_DIR, exist_ok=True)
    
    yield
    
    # Cleanup can be done here if needed


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Make test result available to fixtures."""
    outcome = yield
    rep = outcome.get_result()
    
    # Store test failure information
    if rep.when == "call" and rep.failed:
        if not hasattr(pytest, "_test_failed"):
            pytest._test_failed = {}
        pytest._test_failed["name"] = item.name
        pytest._test_failed["failed"] = True