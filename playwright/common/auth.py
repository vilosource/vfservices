"""
Authentication utility for Playwright tests.
Provides reusable login/logout functionality with automatic cleanup.
"""
import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from contextlib import contextmanager
from typing import Optional, Dict, Any, Union
from playwright.sync_api import Page, BrowserContext, TimeoutError
import time


class AuthenticationError(Exception):
    """Raised when authentication fails"""
    pass


class AuthenticatedPage:
    """
    A wrapper around Playwright Page that handles authentication automatically.
    """
    
    def __init__(self, page: Page, username: str, password: str, 
                 base_url: str = "https://identity.vfservices.viloforge.com",
                 service_url: Optional[str] = None):
        self.page = page
        self.username = username
        self.password = password
        self.base_url = base_url
        self.service_url = service_url
        self.logged_in = False
        self._original_context = page.context
        
    def login(self) -> None:
        """Perform login operation"""
        try:
            print(f"Logging in as {self.username}...")
            
            # Navigate to login page
            login_url = f"{self.base_url}/login/"
            self.page.goto(login_url, wait_until="networkidle", timeout=30000)
            
            # Check if already logged in (might have active session)
            if "/login" not in self.page.url and "/accounts/login/" not in self.page.url:
                print(f"Already logged in, current URL: {self.page.url}")
                self.logged_in = True
                return
            
            # Fill login form
            if self.page.locator('input[name="username"]').count() > 0:
                self.page.fill('input[name="username"]', self.username)
                self.page.fill('input[name="password"]', self.password)
            elif self.page.locator('input[name="email"]').count() > 0:
                self.page.fill('input[name="email"]', self.username)
                self.page.fill('input[name="password"]', self.password)
            else:
                raise AuthenticationError("Could not find login form fields")
            
            # Submit login form
            submit_button = self.page.locator('button[type="submit"]').first
            submit_button.click()
            
            # Wait for navigation
            self.page.wait_for_load_state("networkidle", timeout=30000)
            
            # Verify login success
            if "/login" in self.page.url or "/accounts/login/" in self.page.url:
                # Check for error messages
                error_messages = []
                for selector in ['.alert-danger', '.error', '.errorlist', '.alert-error']:
                    if self.page.locator(selector).count() > 0:
                        error_messages.append(self.page.locator(selector).first.inner_text())
                
                error_msg = f"Login failed for user {self.username}"
                if error_messages:
                    error_msg += f": {'; '.join(error_messages)}"
                raise AuthenticationError(error_msg)
            
            # If service URL is provided, navigate there
            if self.service_url:
                self.page.goto(self.service_url, wait_until="networkidle", timeout=30000)
                
                # Check if we were redirected back to login
                if "/login" in self.page.url or "/accounts/login/" in self.page.url:
                    raise AuthenticationError(f"User {self.username} does not have access to {self.service_url}")
            
            self.logged_in = True
            print(f"Successfully logged in as {self.username}")
            
            # Verify JWT token exists
            cookies = self._original_context.cookies()
            jwt_exists = any(c['name'] in ['jwt', 'jwt_token', 'access_token'] for c in cookies)
            if jwt_exists:
                print("JWT token confirmed in cookies")
            
        except TimeoutError:
            raise AuthenticationError(f"Login timeout for user {self.username}")
        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(f"Login failed for user {self.username}: {str(e)}")
    
    def logout(self) -> None:
        """Perform logout operation"""
        if not self.logged_in:
            return
            
        try:
            print(f"Logging out user {self.username}...")
            
            # Try to find logout link
            logout_link = None
            logout_selectors = [
                'a[href*="logout"]',
                'a:has-text("Logout")',
                'a:has-text("Sign Out")',
                'a:has-text("Log Out")',
                '.navbar a[href*="logout"]',
                'nav a[href*="logout"]',
                '.dropdown-menu a[href*="logout"]'
            ]
            
            for selector in logout_selectors:
                try:
                    if self.page.locator(selector).count() > 0:
                        logout_link = self.page.locator(selector).first
                        if logout_link.is_visible():
                            logout_link.click()
                            self.page.wait_for_load_state("networkidle", timeout=10000)
                            break
                except:
                    continue
            
            # If no logout link found, navigate directly
            if not logout_link:
                logout_url = f"{self.base_url}/logout/"
                if self.service_url and "cielo" in self.service_url:
                    logout_url = f"{self.service_url.rstrip('/')}/accounts/logout/"
                elif self.service_url:
                    logout_url = f"{self.service_url.rstrip('/')}/logout/"
                    
                self.page.goto(logout_url, wait_until="networkidle", timeout=30000)
            
            # Handle logout confirmation if needed
            if self.page.locator('button:has-text("Yes, Logout")').count() > 0:
                self.page.click('button:has-text("Yes, Logout")')
                self.page.wait_for_load_state("networkidle", timeout=10000)
            elif self.page.locator('button:has-text("Logout")').count() > 0:
                self.page.click('button:has-text("Logout")')
                self.page.wait_for_load_state("networkidle", timeout=10000)
            
            self.logged_in = False
            print(f"Successfully logged out user {self.username}")
            
        except Exception as e:
            print(f"Warning: Logout may have failed for {self.username}: {str(e)}")
    
    def get_jwt_token(self) -> Optional[str]:
        """Extract JWT token from cookies or local storage"""
        # Check cookies first
        cookies = self._original_context.cookies()
        for cookie in cookies:
            if cookie['name'] in ['jwt', 'jwt_token', 'access_token']:
                return cookie['value']
        
        # Check local storage
        try:
            token = self.page.evaluate("() => localStorage.getItem('jwt_token') || localStorage.getItem('access_token')")
            if token:
                return token
        except:
            pass
        
        return None
    
    def __getattr__(self, name):
        """Proxy all other attributes to the underlying Page object"""
        return getattr(self.page, name)


@contextmanager
def authenticated_page(page: Page, username: str, password: Optional[str] = None,
                      base_url: str = "https://identity.vfservices.viloforge.com",
                      service_url: Optional[str] = None):
    """
    Context manager for authenticated page access.
    
    Usage:
        with authenticated_page(page, "alice", "alice123!#QWERT") as auth_page:
            auth_page.goto("https://website.vfservices.viloforge.com/admin/")
            # ... perform tests ...
        # Automatic logout happens here
    
    Args:
        page: Playwright Page object
        username: Username for login
        password: Password for login (defaults to {username}123!#QWERT if not provided)
        base_url: Base URL for identity provider (default: https://identity.vfservices.viloforge.com)
        service_url: Optional service URL to navigate to after login
    
    Yields:
        AuthenticatedPage object that proxies to the Page object
    """
    if password is None:
        password = f"{username}123!#QWERT"
    
    auth_page = AuthenticatedPage(page, username, password, base_url, service_url)
    
    try:
        auth_page.login()
        yield auth_page
    finally:
        auth_page.logout()


def login_user(page: Page, username: str, password: Optional[str] = None,
               base_url: str = "https://identity.vfservices.viloforge.com",
               service_url: Optional[str] = None) -> AuthenticatedPage:
    """
    Standalone login function that returns an AuthenticatedPage.
    Remember to call logout() when done!
    
    Args:
        page: Playwright Page object
        username: Username for login
        password: Password for login (defaults to {username}123!#QWERT if not provided)
        base_url: Base URL for identity provider
        service_url: Optional service URL to navigate to after login
    
    Returns:
        AuthenticatedPage object
    """
    if password is None:
        password = f"{username}123!#QWERT"
    
    auth_page = AuthenticatedPage(page, username, password, base_url, service_url)
    auth_page.login()
    return auth_page


def logout_user(auth_page: Union[AuthenticatedPage, Page]) -> None:
    """
    Standalone logout function.
    
    Args:
        auth_page: Either an AuthenticatedPage object or a regular Page object
    """
    if isinstance(auth_page, AuthenticatedPage):
        auth_page.logout()
    else:
        # Create a temporary AuthenticatedPage just for logout
        temp_auth = AuthenticatedPage(auth_page, "", "")
        temp_auth.logged_in = True  # Force logout attempt
        temp_auth.logout()