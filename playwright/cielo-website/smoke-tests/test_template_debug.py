"""
Debug test to check if the template tag is working.
"""
import pytest
from playwright.sync_api import Page


def test_debug_template_tag(page: Page):
    """Debug test to check template rendering."""
    
    # Add some JavaScript to check if the template is rendered correctly
    page.goto("https://website.vfservices.viloforge.com/accounts/login/")
    
    # Check the HTML source
    html_source = page.content()
    
    # Check if rbac_tags is loaded
    if "{% load rbac_tags %}" in html_source:
        print("❌ Template tag not processed - raw Django template visible")
    else:
        print("✅ Template is processed")
    
    # Login as admin
    page.fill('input[name="email"]', 'admin')
    page.fill('input[name="password"]', 'admin123')
    page.click('button[type="submit"]')
    page.wait_for_function("!window.location.href.includes('/accounts/login')", timeout=10000)
    
    # Get the page source after login
    html_after_login = page.content()
    
    # Check for template tag remnants
    if "user_has_role" in html_after_login:
        print("⚠️  Found 'user_has_role' in HTML - template tag might not be working")
    
    # Check if Identity Admin text exists anywhere
    if "Identity Admin" in html_after_login:
        print("✅ Found 'Identity Admin' text in page")
    else:
        print("❌ 'Identity Admin' text not found in page")
    
    # Save the page source for manual inspection
    with open("page_source_debug.html", "w") as f:
        f.write(html_after_login)
    print("📄 Page source saved to page_source_debug.html")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])