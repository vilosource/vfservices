#!/usr/bin/env python3
"""Comprehensive test suite for Identity Admin functionality"""

import sys
sys.path.append('/home/jasonvi/GitHub/vfservices')

from playwright.sync_api import sync_playwright
import time

class IdentityAdminTestSuite:
    """Comprehensive test suite for Identity Admin"""
    
    def __init__(self):
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
    
    def log_result(self, test_name, passed, details=""):
        """Log test result"""
        if passed:
            self.passed_tests += 1
            status = "✓ PASSED"
        else:
            self.failed_tests += 1
            status = "✗ FAILED"
        
        result = f"{status} - {test_name}"
        if details:
            result += f" ({details})"
        
        print(result)
        self.test_results.append(result)
    
    def run_all_tests(self):
        """Run all Identity Admin tests"""
        print("=" * 80)
        print("IDENTITY ADMIN COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                ignore_https_errors=True
            )
            page = context.new_page()
            
            try:
                # Test 1: Authentication
                print("\n[Test 1] Authentication and Authorization")
                print("-" * 40)
                self.test_authentication(page)
                
                # Test 2: Dashboard
                print("\n[Test 2] Dashboard Functionality")
                print("-" * 40)
                self.test_dashboard(page)
                
                # Test 3: User List
                print("\n[Test 3] User List View")
                print("-" * 40)
                self.test_user_list(page)
                
                # Test 4: User Detail
                print("\n[Test 4] User Detail View")
                print("-" * 40)
                self.test_user_detail(page)
                
                # Test 5: User Edit
                print("\n[Test 5] User Edit Functionality")
                print("-" * 40)
                self.test_user_edit(page)
                
                # Test 6: Role Management
                print("\n[Test 6] Role Management")
                print("-" * 40)
                self.test_role_management(page)
                
                # Test 7: Navigation
                print("\n[Test 7] Navigation and UI Elements")
                print("-" * 40)
                self.test_navigation(page)
                
                # Test 8: Search and Filter
                print("\n[Test 8] Search and Filter Functionality")
                print("-" * 40)
                self.test_search_filter(page)
                
            finally:
                browser.close()
        
        # Print summary
        self.print_summary()
    
    def test_authentication(self, page):
        """Test authentication and authorization"""
        # Test login
        page.goto("https://identity.vfservices.viloforge.com/login/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='username']", "admin")
        page.fill("input[name='password']", "admin123")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        
        self.log_result("Admin login", "login" not in page.url)
        
        # Test access to Identity Admin
        response = page.goto("https://website.vfservices.viloforge.com/admin/")
        self.log_result("Access Identity Admin", response.status == 200)
        
        # Test that JWT token exists
        cookies = page.context.cookies()
        jwt_exists = any(c['name'] in ['jwt', 'jwt_token'] for c in cookies)
        self.log_result("JWT token present", jwt_exists)
    
    def test_dashboard(self, page):
        """Test dashboard functionality"""
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Check page title
        title = page.title()
        self.log_result("Dashboard title", "Identity Administration" in title)
        
        # Check main sections
        sections = [
            ("Welcome message", "Welcome to Identity Administration"),
            ("User Management section", "User Management"),
            ("Role Assignment section", "Role Assignment"),
            ("Service Registry section", "Service Registry")
        ]
        
        content = page.inner_text(".content-page")
        for section_name, section_text in sections:
            self.log_result(section_name, section_text in content)
        
        # Check navigation menu
        menu_items = ["Dashboard", "Users", "Roles", "Services"]
        for item in menu_items:
            exists = page.query_selector(f"a:has-text('{item}')") is not None
            self.log_result(f"Menu item: {item}", exists)
    
    def test_user_list(self, page):
        """Test user list view"""
        page.goto("https://website.vfservices.viloforge.com/admin/users/")
        page.wait_for_load_state("networkidle")
        
        # Check page loaded
        self.log_result("User list page loaded", page.title() == "User Management | Identity Admin")
        
        # Check table exists
        table = page.query_selector("#userTable")
        self.log_result("User table exists", table is not None)
        
        # Count users
        rows = page.query_selector_all("#userTable tbody tr")
        self.log_result("Users displayed", len(rows) > 0, f"{len(rows)} users found")
        
        # Check for specific users
        users = ["admin", "alice"]
        for username in users:
            exists = page.query_selector(f"td:has-text('{username}')") is not None
            self.log_result(f"User '{username}' in list", exists)
        
        # Check action buttons
        actions = ["Create User", "Search", "Apply Filters"]
        for action in actions:
            if action == "Search":
                exists = page.query_selector("#searchInput") is not None
            elif action == "Create User":
                exists = page.query_selector(f"a:has-text('{action}')") is not None
            else:
                exists = page.query_selector(f"button:has-text('{action}')") is not None
            self.log_result(f"Action: {action}", exists)
    
    def test_user_detail(self, page):
        """Test user detail view"""
        # Navigate to alice's detail page
        page.goto("https://website.vfservices.viloforge.com/admin/users/8/")
        page.wait_for_load_state("networkidle")
        
        # Check if we're on the detail page
        on_detail_page = "alice" in page.title()
        self.log_result("User detail page loaded", on_detail_page)
        
        if on_detail_page:
            # Check user information
            elements = [
                ("Username", "h4:has-text('Alice User')"),
                ("Email", "span:has-text('alice@example.com')"),
                ("Status badge", ".badge:has-text('Active')"),
                ("Roles section", "h5:has-text('Assigned Roles')")
            ]
            
            for element_name, selector in elements:
                exists = page.query_selector(selector) is not None
                self.log_result(f"Detail: {element_name}", exists)
            
            # Check action buttons
            buttons = ["Edit User", "Manage Roles", "Back to List"]
            for button in buttons:
                exists = page.query_selector(f"a:has-text('{button}')") is not None
                self.log_result(f"Button: {button}", exists)
    
    def test_user_edit(self, page):
        """Test user edit functionality"""
        # Navigate to alice's edit page
        page.goto("https://website.vfservices.viloforge.com/admin/users/8/edit/")
        page.wait_for_load_state("networkidle")
        
        # Check if we're on the edit page
        on_edit_page = "Edit alice" in page.title()
        self.log_result("User edit page loaded", on_edit_page)
        
        if on_edit_page:
            # Check form fields
            fields = [
                ("Username field", "input#username"),
                ("Email field", "input#email"),
                ("First name field", "input#first_name"),
                ("Last name field", "input#last_name"),
                ("Active checkbox", "input#is_active"),
                ("Password fields", "input#new_password")
            ]
            
            for field_name, selector in fields:
                exists = page.query_selector(selector) is not None
                self.log_result(f"Edit field: {field_name}", exists)
            
            # Check that username field is readonly
            username_field = page.query_selector("input#username")
            if username_field:
                is_readonly = username_field.is_disabled() or username_field.get_attribute("readonly") is not None
                self.log_result("Username field readonly", is_readonly)
    
    def test_role_management(self, page):
        """Test role management functionality"""
        # Navigate to alice's role management page
        page.goto("https://website.vfservices.viloforge.com/admin/users/8/roles/")
        page.wait_for_load_state("networkidle")
        
        # Check page loaded
        on_roles_page = "Manage Roles" in page.title()
        self.log_result("Role management page loaded", on_roles_page)
        
        if on_roles_page:
            # Check current roles
            role_rows = page.query_selector_all("table tbody tr")
            self.log_result("Current roles displayed", len(role_rows) > 0, f"{len(role_rows)} roles")
            
            # Check role assignment form
            elements = [
                ("Service selector", "select#service"),
                ("Role selector", "select#role"),
                ("Assign button", "button:has-text('Assign Role')"),
                ("Quick assignment section", "h5:has-text('Quick Assignment')")
            ]
            
            for element_name, selector in elements:
                exists = page.query_selector(selector) is not None
                self.log_result(f"Role form: {element_name}", exists)
            
            # Test service selection interaction
            page.select_option("select#service", "billing_api")
            page.wait_for_timeout(500)
            role_select = page.query_selector("select#role")
            if role_select:
                is_enabled = not role_select.is_disabled()
                self.log_result("Role selector enables on service selection", is_enabled)
    
    def test_navigation(self, page):
        """Test navigation between pages"""
        # Start at dashboard
        page.goto("https://website.vfservices.viloforge.com/admin/")
        page.wait_for_load_state("networkidle")
        
        # Test navigation to Users
        users_link = page.query_selector("a[href*='users/']")
        if users_link:
            users_link.click()
            page.wait_for_load_state("networkidle")
            on_users_page = "User Management" in page.title()
            self.log_result("Navigate to Users", on_users_page)
        
        # Test navigation back to Dashboard
        dashboard_link = page.query_selector("a[href*='dashboard']")
        if dashboard_link:
            dashboard_link.click()
            page.wait_for_load_state("networkidle")
            on_dashboard = "Identity Administration" in page.title()
            self.log_result("Navigate back to Dashboard", on_dashboard)
        
        # Test logout link exists
        logout_link = page.query_selector("a[href*='logout']")
        self.log_result("Logout link present", logout_link is not None)
    
    def test_search_filter(self, page):
        """Test search and filter functionality"""
        page.goto("https://website.vfservices.viloforge.com/admin/users/")
        page.wait_for_load_state("networkidle")
        
        # Test search input
        search_input = page.query_selector("#searchInput")
        if search_input:
            # Type search term
            search_input.fill("alice")
            self.log_result("Search input accepts text", True)
            
            # Test filter selects
            status_filter = page.query_selector("#statusFilter")
            self.log_result("Status filter present", status_filter is not None)
            
            role_filter = page.query_selector("#roleFilter")
            self.log_result("Role filter present", role_filter is not None)
            
            # Test apply filters button
            apply_button = page.query_selector("#applyFilters")
            self.log_result("Apply filters button present", apply_button is not None)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total_tests = self.passed_tests + self.failed_tests
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests} ({self.passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {self.failed_tests} ({self.failed_tests/total_tests*100:.1f}%)")
        
        if self.failed_tests > 0:
            print("\nFailed Tests:")
            for result in self.test_results:
                if "✗ FAILED" in result:
                    print(f"  {result}")
        
        print("\n" + ("✓ ALL TESTS PASSED!" if self.failed_tests == 0 else "✗ SOME TESTS FAILED!"))
        print("=" * 80)

if __name__ == "__main__":
    suite = IdentityAdminTestSuite()
    suite.run_all_tests()