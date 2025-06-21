import pytest
from playwright.sync_api import Page, expect
import os

# Test user credentials
TEST_USER = "alice"
TEST_PASSWORD = "password123"
BASE_URL = "https://cielo.viloforge.com"

def test_login_redirect_to_homepage(page: Page):
    """Test that login without a next parameter redirects to homepage."""
    # Clear any existing cookies
    page.context.clear_cookies()
    
    # Navigate directly to login page
    page.goto(f"{BASE_URL}/accounts/login/")
    
    # Fill in login form
    page.fill('input[name="email"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASSWORD)
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Wait for redirect and verify we're on the homepage
    page.wait_for_url(f"{BASE_URL}/")
    expect(page).to_have_url(f"{BASE_URL}/")
    
    # Verify we're authenticated by checking that we're on the homepage
    # and not redirected back to login
    expect(page).not_to_have_url(f"{BASE_URL}/accounts/login/")

def test_login_redirect_with_next_parameter(page: Page):
    """Test that login with a next parameter redirects to the specified page."""
    # Clear any existing cookies
    page.context.clear_cookies()
    
    # Try to access a protected page (should redirect to login with next parameter)
    page.goto(f"{BASE_URL}/management/")
    
    # Should be redirected to login page with next parameter
    expect(page).to_have_url(f"{BASE_URL}/accounts/login/?next=/management/")
    
    # Fill in login form
    page.fill('input[name="email"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASSWORD)
    
    # Submit form
    page.click('button[type="submit"]')
    
    # Wait for redirect and verify we're on the management page
    page.wait_for_url(f"{BASE_URL}/management/")
    expect(page).to_have_url(f"{BASE_URL}/management/")
    
    # Verify we're authenticated by checking we stayed on the management page
    # and didn't get redirected back to login
    expect(page).not_to_have_url(f"{BASE_URL}/accounts/login/")

def test_authenticated_user_accessing_login_redirects_home(page: Page):
    """Test that an already authenticated user accessing login page is redirected to homepage."""
    # Clear cookies and login first
    page.context.clear_cookies()
    page.goto(f"{BASE_URL}/accounts/login/")
    page.fill('input[name="email"]', TEST_USER)
    page.fill('input[name="password"]', TEST_PASSWORD)
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/")
    
    # Now try to access login page again while authenticated
    page.goto(f"{BASE_URL}/accounts/login/")
    
    # Should be redirected to homepage
    expect(page).to_have_url(f"{BASE_URL}/")