from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.core.cache import cache
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
