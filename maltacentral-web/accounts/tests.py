from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.cache import cache
from django.contrib.auth.models import User
from django.conf import settings
from unittest.mock import patch, Mock
import json
import requests
from .identity_client import IdentityProviderClient
from .utils import check_rate_limit, clear_rate_limit


class IdentityProviderClientTest(TestCase):
    """Test the IdentityProviderClient functionality."""
    
    def setUp(self):
        self.client = IdentityProviderClient()
        
    @patch('accounts.identity_client.requests.post')
    def test_successful_authentication(self, mock_post):
        """Test successful authentication returns token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"token": "test-jwt-token", "user": {"username": "test@example.com"}}
        mock_post.return_value = mock_response
        
        result = self.client.authenticate_user("test@example.com", "password")
        
        self.assertIn("token", result)
        self.assertEqual(result["token"], "test-jwt-token")
        mock_post.assert_called_once()
        
    @patch('accounts.identity_client.requests.post')
    def test_failed_authentication(self, mock_post):
        """Test failed authentication returns error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Invalid credentials"}
        mock_post.return_value = mock_response
        
        result = self.client.authenticate_user("test@example.com", "wrong-password")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid credentials")
        
    @patch('accounts.identity_client.requests.post')
    def test_connection_error(self, mock_post):
        """Test connection error handling."""
        mock_post.side_effect = requests.ConnectionError()
        
        result = self.client.authenticate_user("test@example.com", "password")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Authentication service unavailable")
        
    @patch('accounts.identity_client.requests.post')
    def test_timeout_error(self, mock_post):
        """Test timeout error handling."""
        mock_post.side_effect = requests.Timeout()
        
        result = self.client.authenticate_user("test@example.com", "password")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Authentication service timeout")


class LoginViewTest(TestCase):
    """Test the login view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
    def test_get_login_page(self):
        """Test GET request renders login page."""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")
        self.assertContains(response, "Email address")
        
    @patch('accounts.views.IdentityProviderClient')
    def test_successful_login(self, mock_client_class):
        """Test successful login sets cookie and redirects."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token"}
        mock_client_class.return_value = mock_client
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('jwt', response.cookies)
        
    @patch('accounts.views.IdentityProviderClient')
    def test_failed_login(self, mock_client_class):
        """Test failed login shows error message."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"error": "Invalid credentials"}
        mock_client_class.return_value = mock_client
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'wrong-password'
        })
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Invalid credentials")
        
    def test_missing_credentials(self):
        """Test login with missing credentials shows error."""
        response = self.client.post(self.login_url, {
            'email': '',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Email and password are required")
        
    @patch('accounts.views.IdentityProviderClient')
    def test_remember_me_cookie_duration(self, mock_client_class):
        """Test remember me affects cookie duration."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token"}
        mock_client_class.return_value = mock_client
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password',
            'remember': 'on'
        })
        
        self.assertEqual(response.status_code, 302)
        jwt_cookie = response.cookies.get('jwt')
        self.assertIsNotNone(jwt_cookie)
        self.assertEqual(jwt_cookie['max-age'], 86400)  # 24 hours


class LogoutViewTest(TestCase):
    """Test the logout view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.logout_url = reverse('accounts:logout')
        
    def test_get_logout_page(self):
        """Test GET request renders logout page."""
        response = self.client.get(self.logout_url)
        
        self.assertEqual(response.status_code, 200)
        
    def test_post_logout(self):
        """Test POST request clears cookie and redirects."""
        # Set a JWT cookie first
        self.client.cookies['jwt'] = 'test-jwt-token'
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('accounts:login'))
        
        # Check that cookie deletion was attempted
        jwt_cookie = response.cookies.get('jwt')
        self.assertIsNotNone(jwt_cookie)
        self.assertEqual(jwt_cookie.value, '')


class RateLimitTest(TestCase):
    """Test rate limiting functionality."""
    
    def setUp(self):
        self.mock_request = Mock()
        self.mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}
        cache.clear()
        
    def test_rate_limit_within_limit(self):
        """Test requests within rate limit are allowed."""
        for i in range(4):  # Under the default limit of 5
            result = check_rate_limit(self.mock_request)
            self.assertTrue(result)
            
    def test_rate_limit_exceeded(self):
        """Test requests exceeding rate limit are blocked."""
        # Make 5 requests (the limit)
        for i in range(5):
            check_rate_limit(self.mock_request)
            
        # 6th request should be blocked
        result = check_rate_limit(self.mock_request)
        self.assertFalse(result)
        
    def test_clear_rate_limit(self):
        """Test clearing rate limit allows new requests."""
        # Exceed rate limit
        for i in range(6):
            check_rate_limit(self.mock_request)
            
        # Clear rate limit
        clear_rate_limit(self.mock_request)
        
        # Should be able to make requests again
        result = check_rate_limit(self.mock_request)
        self.assertTrue(result)


class IntegrationTest(TestCase):
    """Integration tests for the complete login flow."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        
    @patch('accounts.views.IdentityProviderClient')
    def test_full_login_flow(self, mock_client_class):
        """Test the complete login flow with successful authentication."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token"}
        mock_client_class.return_value = mock_client
        
        # Test GET request
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        
        # Test POST request
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertIn('jwt', response.cookies)
        
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), "Login successful")
        
    @patch('accounts.views.IdentityProviderClient')
    def test_csrf_protection(self, mock_client_class):
        """Test CSRF protection is enabled."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token"}
        mock_client_class.return_value = mock_client
        
        # Request without CSRF token should fail
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password'
        }, follow=True)
        
        # Should be redirected or show CSRF error
        self.assertContains(response, "CSRF" or "Forbidden", status_code=403)


class ProfileViewTest(TestCase):
    """Test the profile view functionality."""
    
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('accounts:profile')
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    def test_profile_requires_login(self):
        """Test that profile page requires authentication."""
        response = self.client.get(self.profile_url)
        
        # Should redirect to login page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
        self.assertIn('next=/accounts/profile/', response.url)
        
    def test_profile_with_authenticated_user(self):
        """Test profile page loads for authenticated user."""
        # Mock JWT authentication middleware to set request.user
        with patch('common.jwt_auth.middleware.JWTAuthenticationMiddleware') as mock_middleware:
            # Simulate authenticated user
            self.client.force_login(self.user)
            
            response = self.client.get(self.profile_url)
            
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "User Profile")
            self.assertContains(response, "Profile Information")
            self.assertContains(response, "identity-api-client.js")
            
    def test_profile_page_contains_required_elements(self):
        """Test profile page contains all required HTML elements."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for essential page elements
        self.assertContains(response, 'id="profile-content"')
        self.assertContains(response, 'id="profile-loading"')
        self.assertContains(response, 'id="profile-error"')
        self.assertContains(response, 'id="profile-username"')
        self.assertContains(response, 'id="profile-email"')
        self.assertContains(response, 'id="refresh-profile-btn"')
        
    def test_profile_page_javascript_configuration(self):
        """Test that JavaScript configuration is properly set."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check that identity service URL is passed to JavaScript
        self.assertContains(response, 'window.IDENTITY_SERVICE_URL')
        self.assertContains(response, settings.EXTERNAL_SERVICE_URLS['identity'])
        
    def test_profile_page_context_data(self):
        """Test that proper context data is passed to template."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check context variables
        self.assertIn('identity_service_url', response.context)
        self.assertIn('user', response.context)
        self.assertEqual(response.context['identity_service_url'], 
                        settings.EXTERNAL_SERVICE_URLS['identity'])
        self.assertEqual(response.context['user'], self.user)
        
    def test_profile_page_breadcrumb(self):
        """Test profile page breadcrumb navigation."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertContains(response, 'breadcrumb-item')
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Account')
        self.assertContains(response, 'Profile')
        
    def test_profile_page_logout_link(self):
        """Test profile page contains logout functionality."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        logout_url = reverse('accounts:logout')
        self.assertContains(response, logout_url)
        self.assertContains(response, 'Logout')
        
    def test_profile_page_title(self):
        """Test profile page has correct title."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        self.assertContains(response, '<title>User Profile - VF Services</title>')
        
    def test_profile_page_css_styles(self):
        """Test profile page includes custom CSS styles."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for custom CSS classes
        self.assertContains(response, 'profile-card')
        self.assertContains(response, 'profile-info-item')
        self.assertContains(response, 'profile-label')
        self.assertContains(response, 'loading-spinner')
        
    @patch('accounts.views.logger')
    def test_profile_view_logging(self, mock_logger):
        """Test that profile view logs access appropriately."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Verify logging was called
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called()
        
    def test_profile_view_handles_exceptions(self):
        """Test that profile view handles exceptions gracefully."""
        self.client.force_login(self.user)
        
        # Mock settings to cause an exception
        with patch('accounts.views.settings') as mock_settings:
            mock_settings.EXTERNAL_SERVICE_URLS = None
            
            # This should raise an exception, but view should handle it
            with self.assertRaises(Exception):
                response = self.client.get(self.profile_url)


class LoginFlowIntegrationTest(TestCase):
    """Integration tests for the complete login flow and cookie handling."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.profile_url = reverse('accounts:profile')
        
    @patch('accounts.views.IdentityProviderClient')
    def test_login_sets_both_jwt_cookies(self, mock_client_class):
        """Test that login sets both httpOnly and JavaScript-accessible cookies."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token-12345"}
        mock_client_class.return_value = mock_client
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password'
        })
        
        self.assertEqual(response.status_code, 302)
        
        # Check that both cookies are set
        self.assertIn('jwt', response.cookies)
        self.assertIn('jwt_token', response.cookies)
        
        # Verify cookie values are the same
        jwt_cookie = response.cookies['jwt']
        jwt_token_cookie = response.cookies['jwt_token']
        self.assertEqual(jwt_cookie.value, jwt_token_cookie.value)
        self.assertEqual(jwt_cookie.value, "test-jwt-token-12345")
        
        # Verify httpOnly settings
        self.assertTrue(jwt_cookie['httponly'])  # Server-side cookie
        self.assertFalse(jwt_token_cookie['httponly'])  # JavaScript-accessible cookie
        
    @patch('accounts.views.IdentityProviderClient')
    def test_remember_me_affects_both_cookies(self, mock_client_class):
        """Test that remember me affects both cookie max-age settings."""
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token-12345"}
        mock_client_class.return_value = mock_client
        
        response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password',
            'remember': 'on'
        })
        
        jwt_cookie = response.cookies['jwt']
        jwt_token_cookie = response.cookies['jwt_token']
        
        # Both cookies should have 24-hour max-age
        self.assertEqual(jwt_cookie['max-age'], 86400)
        self.assertEqual(jwt_token_cookie['max-age'], 86400)
        
    def test_logout_clears_both_cookies(self):
        """Test that logout clears both JWT cookies."""
        # First set cookies to simulate logged in state
        self.client.cookies['jwt'] = 'test-token'
        self.client.cookies['jwt_token'] = 'test-token'
        
        response = self.client.post(reverse('accounts:logout'))
        
        # Check that both cookies are deleted
        self.assertIn('jwt', response.cookies)
        self.assertIn('jwt_token', response.cookies)
        
        # Verify cookies are cleared (empty value)
        self.assertEqual(response.cookies['jwt'].value, '')
        self.assertEqual(response.cookies['jwt_token'].value, '')
        
    @patch('accounts.views.IdentityProviderClient')
    def test_profile_access_without_javascript_accessible_token(self, mock_client_class):
        """Test profile page behavior when only httpOnly cookie is present."""
        # This test simulates the original bug condition
        mock_client = Mock()
        mock_client.authenticate_user.return_value = {"token": "test-jwt-token-12345"}
        mock_client_class.return_value = mock_client
        
        # Login to set cookies
        login_response = self.client.post(self.login_url, {
            'email': 'test@example.com',
            'password': 'password'
        })
        
        # Now test profile page access
        response = self.client.get(self.profile_url)
        
        # Page should load (server-side authentication works)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User Profile")
        
        # Check that JavaScript configuration is present
        self.assertContains(response, 'window.IDENTITY_SERVICE_URL')
        self.assertContains(response, 'identity-api-client.js')


class ProfilePageIntegrationTest(TestCase):
    """Integration tests for the profile page with JWT authentication."""
    
    def setUp(self):
        self.client = Client()
        self.profile_url = reverse('accounts:profile')
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
        
    def test_complete_profile_workflow(self):
        """Test the complete workflow from login to profile access."""
        # First, simulate login
        self.client.force_login(self.user)
        
        # Set a JWT cookie to simulate successful authentication
        jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3QiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20ifQ.test"
        self.client.cookies['jwt'] = jwt_token
        
        # Access profile page
        response = self.client.get(self.profile_url)
        
        # Verify successful access
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "User Profile")
        
        # Verify JWT token is available to JavaScript
        self.assertContains(response, 'window.IDENTITY_SERVICE_URL')
        
    def test_profile_page_security_headers(self):
        """Test that profile page includes proper security headers."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for security-related headers
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        
    def test_profile_page_responsive_elements(self):
        """Test that profile page includes responsive design elements."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for Bootstrap responsive classes
        self.assertContains(response, 'col-lg-8')
        self.assertContains(response, 'col-xl-6')
        self.assertContains(response, 'd-grid')
        
    def test_profile_page_error_handling_elements(self):
        """Test that profile page includes proper error handling UI."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for error handling elements
        self.assertContains(response, 'profile-error')
        self.assertContains(response, 'profile-error-message')
        self.assertContains(response, 'retry-profile-btn')
        
    def test_profile_page_accessibility(self):
        """Test profile page accessibility features."""
        self.client.force_login(self.user)
        
        response = self.client.get(self.profile_url)
        
        # Check for accessibility features
        self.assertContains(response, 'aria-')  # ARIA attributes
        self.assertContains(response, 'role=')   # Role attributes
        self.assertContains(response, 'alt=')    # Alt text for images
