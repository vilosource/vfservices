"""
Playwright configuration for Azure Costs API smoke tests.
"""
import os


# Test configuration
class Config:
    # Base URLs
    AZURE_COSTS_BASE_URL = os.environ.get("AZURE_COSTS_BASE_URL", "https://azure-costs.cielo.viloforge.com")
    IDENTITY_PROVIDER_URL = os.environ.get("IDENTITY_PROVIDER_URL", "https://identity.cielo.viloforge.com")
    CIELO_WEBSITE_URL = os.environ.get("CIELO_WEBSITE_URL", "https://cielo.viloforge.com")
    
    # Test credentials
    TEST_USERNAME = os.environ.get("TEST_USERNAME", "alice")
    TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "password123")
    
    # Browser settings
    HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
    SLOW_MO = int(os.environ.get("SLOW_MO", "0"))  # Milliseconds to slow down operations
    
    # Timeouts
    DEFAULT_TIMEOUT = int(os.environ.get("DEFAULT_TIMEOUT", "30000"))  # 30 seconds
    NAVIGATION_TIMEOUT = int(os.environ.get("NAVIGATION_TIMEOUT", "30000"))  # 30 seconds
    
    # Screenshot settings
    SCREENSHOT_ON_FAILURE = os.environ.get("SCREENSHOT_ON_FAILURE", "true").lower() == "true"
    SCREENSHOT_DIR = os.environ.get("SCREENSHOT_DIR", "./screenshots")
    
    # Video settings
    RECORD_VIDEO = os.environ.get("RECORD_VIDEO", "false").lower() == "true"
    VIDEO_DIR = os.environ.get("VIDEO_DIR", "./videos")
    
    # Retry settings
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.environ.get("RETRY_DELAY", "1000"))  # 1 second
    
    # SSL settings (for local testing)
    IGNORE_HTTPS_ERRORS = os.environ.get("IGNORE_HTTPS_ERRORS", "true").lower() == "true"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests that require authentication"
    )
    config.addinivalue_line(
        "markers", "api: marks API tests"
    )
    config.addinivalue_line(
        "markers", "browser: marks browser-based tests"
    )