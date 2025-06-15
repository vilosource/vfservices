import json
import sys
import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

# Add parent directory to path to import common modules
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.jwt_auth.utils import decode_jwt


class APIInfoViewTests(TestCase):
    """Test cases for the API info endpoint."""
    
    def setUp(self):
        self.client = Client()
    
    def test_api_info_endpoint(self):
        """Test the /api/ endpoint returns correct API information."""
        response = self.client.get('/api/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn('service', data)
        self.assertIn('version', data)
        self.assertIn('endpoints', data)
        self.assertIn('authentication', data)
        self.assertIn('timestamp', data)
        
        # Check service info
        self.assertEqual(data['service'], 'Identity Provider API')
        self.assertEqual(data['version'], '1.0.0')
        
        # Check endpoints structure
        endpoints = data['endpoints']
        self.assertIn('/api/', endpoints)
        self.assertIn('/api/login/', endpoints)
        self.assertIn('/api/status/', endpoints)
        self.assertIn('/api/docs/', endpoints)
        self.assertIn('/api/redoc/', endpoints)
        
        # Check authentication info
        auth = data['authentication']
        self.assertEqual(auth['type'], 'JWT Token')
        self.assertIn('header_format', auth)


class APIStatusViewTests(TestCase):
    """Test cases for the API status endpoint."""
    
    def setUp(self):
        self.client = Client()
    
    def test_api_status_endpoint(self):
        """Test the /api/status/ endpoint returns health status."""
        response = self.client.get('/api/status/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn('status', data)
        self.assertIn('service', data)
        self.assertIn('version', data)
        self.assertIn('timestamp', data)
        
        # Check values
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['service'], 'identity-provider')
        self.assertEqual(data['version'], '1.0.0')


class LoginAPIViewTests(APITestCase):
    """Test cases for the login API endpoint."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.login_url = reverse('api_login')
    
    def test_login_success(self):
        """Test successful login returns JWT token."""
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.json()
        
        # Check token is returned
        self.assertIn('token', response_data)
        token = response_data['token']
        self.assertIsInstance(token, str)
        self.assertTrue(len(token) > 0)
        
        # Verify token can be decoded
        try:
            payload = decode_jwt(token)
            self.assertEqual(payload['username'], 'testuser')
            self.assertEqual(payload['email'], 'test@example.com')
            self.assertIn('iat', payload)
            self.assertIn('exp', payload)
        except Exception as e:
            self.fail(f"Token decoding failed: {e}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials returns 401."""
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Invalid credentials')
    
    def test_login_missing_username(self):
        """Test login without username returns 400."""
        data = {
            'password': 'testpass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Username and password are required')
    
    def test_login_missing_password(self):
        """Test login without password returns 400."""
        data = {
            'username': 'testuser'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Username and password are required')
    
    def test_login_empty_credentials(self):
        """Test login with empty credentials returns 400."""
        data = {
            'username': '',
            'password': ''
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Username and password are required')
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent user returns 401."""
        data = {
            'username': 'nonexistentuser',
            'password': 'somepassword'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], 'Invalid credentials')
    
    def test_login_get_method_not_allowed(self):
        """Test GET request to login endpoint returns 405."""
        response = self.client.get(self.login_url)
        
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class APIDocumentationTests(TestCase):
    """Test cases for API documentation endpoints."""
    
    def setUp(self):
        self.client = Client()
    
    def test_swagger_docs_accessible(self):
        """Test that Swagger documentation is accessible."""
        response = self.client.get('/api/docs/')
        
        # Should return 200 for Swagger UI
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))
    
    def test_redoc_docs_accessible(self):
        """Test that ReDoc documentation is accessible."""
        response = self.client.get('/api/redoc/')
        
        # Should return 200 for ReDoc UI
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))
    
    def test_schema_json_accessible(self):
        """Test that OpenAPI schema JSON is accessible."""
        response = self.client.get('/api/schema/')
        
        # Should return 200 with YAML/JSON schema
        self.assertEqual(response.status_code, 200)
        content_type = response.get('Content-Type', '')
        self.assertTrue(
            'application/json' in content_type or 'application/yaml' in content_type,
            f"Expected JSON or YAML content type, got: {content_type}"
        )
        
        # Should be valid schema content (supports both Swagger 2.0 and OpenAPI 3.0)
        content = response.content.decode('utf-8')
        self.assertTrue(
            'openapi' in content or 'swagger' in content,
            "Schema should contain 'openapi' or 'swagger' version info"
        )
        self.assertIn('info', content)
        self.assertIn('paths', content)


class IntegrationTests(APITestCase):
    """Integration tests for the entire API workflow."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='integrationpass123'
        )
    
    def test_full_authentication_flow(self):
        """Test complete authentication flow from login to token usage."""
        # Step 1: Check API status
        status_response = self.client.get('/api/status/')
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()['status'], 'healthy')
        
        # Step 2: Get API info
        info_response = self.client.get('/api/')
        self.assertEqual(info_response.status_code, 200)
        info_data = info_response.json()
        self.assertIn('/api/login/', info_data['endpoints'])
        
        # Step 3: Login and get token
        login_data = {
            'username': 'integrationuser',
            'password': 'integrationpass123'
        }
        login_response = self.client.post('/api/login/', login_data, format='json')
        self.assertEqual(login_response.status_code, 200)
        
        token = login_response.json()['token']
        self.assertIsInstance(token, str)
        
        # Step 4: Verify token contains correct information
        payload = decode_jwt(token)
        self.assertEqual(payload['username'], 'integrationuser')
        self.assertEqual(payload['email'], 'integration@example.com')
        
        # Step 5: Verify token expiration is set
        self.assertIn('exp', payload)
        self.assertIn('iat', payload)
        self.assertGreater(payload['exp'], payload['iat'])


class ErrorHandlingTests(APITestCase):
    """Test error handling across API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_invalid_json_payload(self):
        """Test API handles invalid JSON gracefully."""
        response = self.client.post(
            '/api/login/',
            'invalid json',
            content_type='application/json'
        )
        
        # Should handle malformed JSON gracefully
        self.assertEqual(response.status_code, 400)
    
    def test_unsupported_media_type(self):
        """Test API handles unsupported content types."""
        response = self.client.post(
            '/api/login/',
            'username=test&password=test',
            content_type='application/x-www-form-urlencoded'
        )
        
        # Should still work with form data
        self.assertIn(response.status_code, [400, 401])  # 400 for missing creds, 401 for invalid creds
    
    def test_large_payload(self):
        """Test API handles large payloads appropriately."""
        large_data = {
            'username': 'a' * 1000,  # Very long username
            'password': 'b' * 1000   # Very long password
        }
        
        response = self.client.post('/api/login/', large_data, format='json')
        
        # Should handle gracefully (likely return 401 for invalid credentials)
        self.assertEqual(response.status_code, 401)


class PerformanceTests(APITestCase):
    """Basic performance tests for API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='perfuser',
            email='perf@example.com',
            password='perfpass123'
        )
    
    def test_multiple_concurrent_requests(self):
        """Test API can handle multiple requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = self.client.get('/api/status/')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == 200 for status_code in results))
        
        # Should complete within reasonable time (5 seconds)
        self.assertLess(end_time - start_time, 5.0)
