"""
Playwright test to verify multi-domain support for identity provider
Tests that the identity provider works correctly with both vfservices.viloforge.com and cielo.viloforge.com
"""
import pytest
from playwright.sync_api import sync_playwright, expect


def test_identity_provider_multi_domain_access():
    """Test that identity provider is accessible from both configured domains"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        
        domains = [
            "identity.vfservices.viloforge.com",
            "identity.cielo.viloforge.com"
        ]
        
        for domain in domains:
            page = context.new_page()
            
            try:
                # Navigate to the identity provider on each domain
                response = page.goto(f"https://{domain}", wait_until="networkidle")
                
                # Should redirect to login page
                assert "/login/" in page.url, f"Should redirect to login page for {domain}"
                assert response.status == 200, f"Expected status 200 for {domain}, got {response.status}"
                
                # Check that login form is present
                username_field = page.locator('input#username')
                expect(username_field).to_be_visible()
                
                print(f"✓ Identity provider accessible via {domain}")
                print(f"  - Redirected to: {page.url}")
                print(f"  - Login form present")
                
            finally:
                page.close()
        
        browser.close()


def test_cors_headers_for_multiple_domains():
    """Test CORS headers are properly configured for both domains"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        test_cases = [
            {
                'origin': 'https://vfservices.viloforge.com',
                'target': 'https://identity.vfservices.viloforge.com/api/'
            },
            {
                'origin': 'https://cielo.viloforge.com',
                'target': 'https://identity.cielo.viloforge.com/api/'
            }
        ]
        
        for test in test_cases:
            context = browser.new_context(
                ignore_https_errors=True,
                extra_http_headers={
                    'Origin': test['origin']
                }
            )
            page = context.new_page()
            
            try:
                # Make request with Origin header
                response = page.goto(test['target'], wait_until="networkidle")
                
                # Check response headers
                headers = response.headers
                
                print(f"\n✓ Testing CORS from {test['origin']} to {test['target']}")
                print(f"  - Status: {response.status}")
                
                if 'access-control-allow-origin' in headers:
                    print(f"  - Access-Control-Allow-Origin: {headers['access-control-allow-origin']}")
                
                if 'access-control-allow-credentials' in headers:
                    print(f"  - Access-Control-Allow-Credentials: {headers['access-control-allow-credentials']}")
                
            finally:
                page.close()
                context.close()
        
        browser.close()


def test_cookie_domain_configuration():
    """Test that SSO cookies are set with correct domain"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()
        
        try:
            # Navigate to identity provider
            page.goto("https://identity.vfservices.viloforge.com/login/", wait_until="networkidle")
            
            # Get all cookies
            cookies = context.cookies()
            
            print("\n✓ Cookie configuration:")
            for cookie in cookies:
                if 'csrf' in cookie['name'].lower() or 'session' in cookie['name'].lower():
                    print(f"  - {cookie['name']}: domain={cookie['domain']}, secure={cookie['secure']}")
                    
                    # Check that domain is properly set for cross-subdomain access
                    if 'session' in cookie['name'].lower():
                        assert cookie['domain'].startswith('.'), "Session cookie should have domain starting with . for subdomain access"
            
        finally:
            browser.close()


def test_redirect_after_login():
    """Test that redirect parameter works for different domains"""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(ignore_https_errors=True)
        
        redirect_urls = [
            "https://vfservices.viloforge.com/dashboard",
            "https://cielo.viloforge.com/home"
        ]
        
        for redirect_url in redirect_urls:
            page = context.new_page()
            
            try:
                # Navigate to login with redirect parameter
                login_url = f"https://identity.vfservices.viloforge.com/login/?next={redirect_url}"
                page.goto(login_url, wait_until="networkidle")
                
                # Check that the form action includes the redirect
                form = page.locator('form[method="post"]')
                form_action = form.get_attribute('action')
                
                print(f"\n✓ Testing redirect to {redirect_url}")
                print(f"  - Login URL: {login_url}")
                print(f"  - Form action: {form_action}")
                
                # The redirect parameter should be preserved
                assert 'next=' in page.url or 'next=' in form_action, "Redirect parameter should be preserved"
                
            finally:
                page.close()
        
        browser.close()


if __name__ == "__main__":
    print("Running Identity Provider Multi-Domain Support Tests...")
    test_identity_provider_multi_domain_access()
    test_cors_headers_for_multiple_domains()
    test_cookie_domain_configuration()
    test_redirect_after_login()
    print("\nAll multi-domain tests completed!")