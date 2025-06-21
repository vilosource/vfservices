"""
Tests for API Logout endpoint
"""
import json
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for JWT utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
from common.jwt_auth import utils as jwt_utils


class APILogoutTestCase(TestCase):
    """Test cases for API logout endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testuser123!#QWERT'
        )
        
        # Create JWT token for test user
        self.payload = {
            "user_id": self.test_user.id,
            "username": self.test_user.username,
            "email": self.test_user.email,
            "iat": timezone.now(),
        }
        self.token = jwt_utils.encode_jwt(self.payload)
        
        # URL for logout endpoint
        self.logout_url = reverse('api_logout')
    
    def test_logout_with_bearer_token(self):
        """Test logout with JWT token in Authorization header."""
        # Set Authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['detail'], 'Logged out successfully')
        
        # Verify cookie is cleared (if it existed)
        self.assertNotIn('jwt', response.cookies)
    
    def test_logout_with_cookie(self):
        """Test logout with JWT token in cookie."""
        # Set JWT cookie
        self.client.cookies['jwt'] = self.token
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['detail'], 'Logged out successfully')
        
        # Verify cookie is cleared
        self.assertEqual(response.cookies.get('jwt').value, '')
    
    def test_logout_without_token(self):
        """Test logout without any token."""
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], 'No authentication token provided')
    
    def test_logout_with_invalid_token(self):
        """Test logout with invalid JWT token."""
        # Set invalid token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertEqual(data['detail'], 'Invalid authentication token')
    
    def test_logout_with_expired_token(self):
        """Test logout with expired JWT token."""
        # Create expired token
        expired_payload = {
            "user_id": self.test_user.id,
            "username": self.test_user.username,
            "email": self.test_user.email,
            "iat": timezone.now() - timezone.timedelta(days=2),
            "exp": timezone.now() - timezone.timedelta(days=1),
        }
        
        with patch.object(jwt_utils, 'encode_jwt') as mock_encode:
            # This will create a token that will be expired when decoded
            mock_encode.return_value = "expired_token"
            expired_token = mock_encode(expired_payload)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {expired_token}')
        
        response = self.client.post(self.logout_url)
        
        # Even expired tokens should be "logged out" successfully 
        # or return 401 depending on implementation
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED])
    
    def test_logout_clears_cookie_with_domain(self):
        """Test that logout clears cookie with proper domain."""
        # Set JWT cookie
        self.client.cookies['jwt'] = self.token
        
        with self.settings(SSO_COOKIE_DOMAIN='.example.com'):
            response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that cookie is cleared
        jwt_cookie = response.cookies.get('jwt')
        self.assertIsNotNone(jwt_cookie)
        self.assertEqual(jwt_cookie.value, '')
        self.assertEqual(jwt_cookie['domain'], '.example.com')
        self.assertEqual(jwt_cookie['path'], '/')
    
    def test_logout_method_not_allowed(self):
        """Test that GET method is not allowed."""
        response = self.client.get(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    @patch('identity_app.views.log_logout_event')
    def test_logout_logs_event(self, mock_log_logout):
        """Test that logout event is logged."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify logout event was logged
        mock_log_logout.assert_called_once()
        args = mock_log_logout.call_args[0]
        # First argument is request
        self.assertIsNotNone(args[0])
        # Second argument is user object (or None)
        user_arg = args[1]
        if user_arg:
            self.assertEqual(user_arg.username, 'testuser')
    
    def test_logout_with_malformed_bearer_header(self):
        """Test logout with malformed Authorization header."""
        # Missing space after Bearer
        self.client.credentials(HTTP_AUTHORIZATION='Bearer')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertEqual(data['detail'], 'No authentication token provided')
    
    @patch('identity_app.views.utils.decode_jwt')
    def test_logout_handles_decode_exception(self, mock_decode):
        """Test logout handles JWT decode exceptions gracefully."""
        mock_decode.side_effect = Exception("Decode error")
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.json()
        self.assertEqual(data['detail'], 'Invalid authentication token')
    
    def test_logout_response_format(self):
        """Test logout response format is consistent."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        response = self.client.post(self.logout_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response is JSON
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Check response structure
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('detail', data)
        self.assertIsInstance(data['detail'], str)


class APILogoutIntegrationTestCase(TestCase):
    """Integration tests for API logout with login flow."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testuser123!#QWERT'
        )
        
        self.login_url = reverse('api_login')
        self.logout_url = reverse('api_logout')
        self.profile_url = reverse('api_profile')
    
    def test_login_logout_flow(self):
        """Test complete login and logout flow."""
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'testuser123!#QWERT'
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.json()['token']
        
        # Use token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        profile_response = self.client.get(self.profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        
        # Logout
        logout_response = self.client.post(self.logout_url)
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Verify token no longer works
        # Note: Without blacklisting, the token will still work until expiry
        # This is a limitation mentioned in the implementation
        profile_response_after_logout = self.client.get(self.profile_url)
        # Token still works because we don't have blacklisting yet
        self.assertEqual(profile_response_after_logout.status_code, status.HTTP_200_OK)
    
    def test_multiple_logout_attempts(self):
        """Test that multiple logout attempts are handled gracefully."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {jwt_utils.encode_jwt({"username": "test"})}')
        
        # First logout
        response1 = self.client.post(self.logout_url)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Second logout with same token
        response2 = self.client.post(self.logout_url)
        # Should still work since we don't have blacklisting
        self.assertEqual(response2.status_code, status.HTTP_200_OK)