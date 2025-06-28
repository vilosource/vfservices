"""Simple login test to debug authentication issues."""

from playwright.sync_api import Page, expect
import time


def test_simple_login(page: Page):
    """Test basic login functionality."""
    
    # Navigate to login page
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    
    # Take screenshot before login
    page.screenshot(path="before_login.png")
    
    # Check if we're on the login page
    assert "login" in page.url.lower()
    
    # Fill in login form
    email_input = page.locator('input[name="email"]')
    password_input = page.locator('input[name="password"]')
    
    # Check if inputs exist
    expect(email_input).to_be_visible()
    expect(password_input).to_be_visible()
    
    # Fill the form
    email_input.fill('admin')
    password_input.fill('admin123')
    
    # Take screenshot after filling
    page.screenshot(path="after_filling.png")
    
    # Find and click submit button
    submit_button = page.locator('button[type="submit"]')
    expect(submit_button).to_be_visible()
    
    # Click submit
    with page.expect_navigation():
        submit_button.click()
    
    # Take screenshot after login attempt
    page.screenshot(path="after_login.png")
    
    # Print the current URL
    print(f"Current URL after login: {page.url}")
    
    # Check if we have any error messages
    error_messages = page.locator('.alert-danger')
    if error_messages.count() > 0:
        print(f"Error message found: {error_messages.first.text_content()}")
    
    # Check if we're logged in (URL should not contain 'login')
    if "login" not in page.url.lower():
        print("Login successful!")
        return True
    else:
        print("Login failed - still on login page")
        return False


if __name__ == "__main__":
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            success = test_simple_login(page)
            print(f"Test result: {'PASSED' if success else 'FAILED'}")
        finally:
            browser.close()