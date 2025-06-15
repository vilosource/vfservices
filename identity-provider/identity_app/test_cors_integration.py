"""
Integration tests for CORS discovery system with Django CORS middleware.

Tests the complete integration between the CORS discovery system and Django's
CORS middleware, verifying that origins are properly validated and CORS headers
are correctly set in HTTP responses.
"""

import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.test.utils import override_settings
from django.urls import reverse


class CORSIntegrationTestCase(TestCase):
    """Base class for CORS integration tests."""
    
    def setUp(self):
        """Set up test client and common test data."""
        self.client = Client()
        
        # Common test endpoints - using existing endpoints
        self.health_url = '/api/'  # API root endpoint
        self.auth_url = '/api/'  # Use API root for testing
        
        # Common test origins
        self.allowed_origin = 'https://www.vfservices.viloforge.com'
        self.malicious_origin = 'https://evil.com'
        self.localhost_origin = 'http://localhost:3000'
    
    def make_cors_request(self, url, origin, method='OPTIONS', **kwargs):
        """Make a CORS request with specified origin."""
        headers = {
            'HTTP_ORIGIN': origin,
            'HTTP_ACCESS_CONTROL_REQUEST_METHOD': 'POST',
            'HTTP_ACCESS_CONTROL_REQUEST_HEADERS': 'content-type'
        }
        headers.update(kwargs)
        
        if method.upper() == 'OPTIONS':
            return self.client.options(url, **headers)
        elif method.upper() == 'GET':
            return self.client.get(url, **headers)
        elif method.upper() == 'POST':
            return self.client.post(url, **headers)
        else:
            raise ValueError(f"Unsupported method: {method}")


class TestCORSAllowedOrigins(CORSIntegrationTestCase):
    """Test CORS behavior with explicitly allowed origins."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com', 'https://api.vfservices.viloforge.com'],
        CORS_ALLOWED_ORIGIN_REGEXES=[]
    )
    def test_cors_allowed_origin_preflight(self):
        """Test that allowed origins receive proper CORS headers in preflight requests."""
        response = self.make_cors_request(self.auth_url, self.allowed_origin)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Access-Control-Allow-Origin'),
            self.allowed_origin
        )
        self.assertIn('POST', response.get('Access-Control-Allow-Methods', ''))
        self.assertIn('content-type', response.get('Access-Control-Allow-Headers', '').lower())
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_ALLOWED_ORIGIN_REGEXES=[]
    )
    def test_cors_allowed_origin_actual_request(self):
        """Test that allowed origins receive CORS headers in actual requests."""
        response = self.make_cors_request(self.health_url, self.allowed_origin, method='GET')
        
        # Note: Actual response status depends on whether the endpoint exists
        self.assertEqual(
            response.get('Access-Control-Allow-Origin'),
            self.allowed_origin
        )
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_ALLOWED_ORIGIN_REGEXES=[]
    )
    def test_cors_denied_origin(self):
        """Test that disallowed origins are rejected."""
        response = self.make_cors_request(self.auth_url, self.malicious_origin)
        
        # Should not have CORS headers for disallowed origins
        self.assertIsNone(response.get('Access-Control-Allow-Origin'))
        self.assertIsNone(response.get('Access-Control-Allow-Methods'))


class TestCORSRegexPatterns(CORSIntegrationTestCase):
    """Test CORS behavior with regex patterns."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=[],
        CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
    )
    def test_cors_regex_pattern_match(self):
        """Test that origins matching regex patterns are allowed."""
        test_origins = [
            'https://api.vfservices.viloforge.com',
            'https://www.vfservices.viloforge.com',
            'https://sub-domain.vfservices.viloforge.com',
        ]
        
        for origin in test_origins:
            with self.subTest(origin=origin):
                response = self.make_cors_request(self.auth_url, origin)
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    response.get('Access-Control-Allow-Origin'),
                    origin
                )
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=[],
        CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
    )
    def test_cors_regex_pattern_rejection(self):
        """Test that origins not matching regex patterns are rejected."""
        test_origins = [
            'http://api.vfservices.viloforge.com',  # HTTP instead of HTTPS
            'https://vfservices.viloforge.com.evil.com',  # Domain hijack attempt
            'https://evil.com',  # Completely different domain
        ]
        
        for origin in test_origins:
            with self.subTest(origin=origin):
                response = self.make_cors_request(self.auth_url, origin)
                
                self.assertIsNone(response.get('Access-Control-Allow-Origin'))


class TestCORSCredentialsHandling(CORSIntegrationTestCase):
    """Test CORS credentials handling."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_ALLOW_CREDENTIALS=True
    )
    def test_cors_credentials_allowed(self):
        """Test that CORS credentials are properly handled when enabled."""
        response = self.make_cors_request(self.auth_url, self.allowed_origin)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Access-Control-Allow-Credentials'),
            'true'
        )
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_ALLOW_CREDENTIALS=False
    )
    def test_cors_credentials_disabled(self):
        """Test CORS behavior when credentials are disabled."""
        response = self.make_cors_request(self.auth_url, self.allowed_origin)
        
        self.assertEqual(response.status_code, 200)
        # Should not have credentials header when disabled
        self.assertNotEqual(
            response.get('Access-Control-Allow-Credentials'),
            'true'
        )


class TestDiscoverySystemIntegration(CORSIntegrationTestCase):
    """Test integration with the CORS discovery system."""
    
    def test_cors_discovery_production_environment(self):
        """Test CORS discovery integration in production environment."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'BASE_DOMAIN': 'vfservices.viloforge.com',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
            'TRAEFIK_HTTP_ROUTERS_WEBSITE_RULE': 'Host(`www.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            # Import and configure CORS discovery
            from identity_app.cors_discovery import configure_cors
            
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                config = configure_cors()
                
                # Verify production configuration
                self.assertIsNotNone(config)
                self.assertEqual(config['environment'], 'production')
                
                # Verify HTTPS-only origins were set
                origins = mock_settings.CORS_ALLOWED_ORIGINS
                self.assertIn('https://identity.vfservices.viloforge.com', origins)
                self.assertIn('https://website.vfservices.viloforge.com', origins)
                
                # Should not include HTTP origins in production
                self.assertNotIn('http://identity.vfservices.viloforge.com', origins)
                self.assertNotIn('http://localhost:3000', origins)
    
    def test_cors_discovery_development_environment(self):
        """Test CORS discovery integration in development environment."""
        env_vars = {
            'ENVIRONMENT': 'development',
            'BASE_DOMAIN': 'dev.vfservices.viloforge.com',
            'LOCAL_CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.dev.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            from identity_app.cors_discovery import configure_cors
            
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                config = configure_cors()
                
                # Verify development configuration
                self.assertIsNotNone(config)
                self.assertEqual(config['environment'], 'development')
                
                # Verify both HTTP and HTTPS origins were set
                origins = mock_settings.CORS_ALLOWED_ORIGINS
                self.assertIn('https://identity.dev.vfservices.viloforge.com', origins)
                self.assertIn('http://identity.dev.vfservices.viloforge.com', origins)
                
                # Should include localhost origins in development
                self.assertIn('http://localhost:3000', origins)
                self.assertIn('http://localhost:8080', origins)
    
    def test_cors_discovery_fallback_configuration(self):
        """Test CORS discovery fallback when Traefik variables are not available."""
        env_vars = {
            'ENVIRONMENT': 'staging',
            'BASE_DOMAIN': 'staging.vfservices.viloforge.com',
            'PEER_SERVICES': 'identity,website,billing',
        }
        
        # Clear any existing Traefik variables
        with patch.dict(os.environ, env_vars, clear=True):
            from identity_app.cors_discovery import configure_cors
            
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                config = configure_cors()
                
                # Verify fallback configuration
                self.assertIsNotNone(config)
                self.assertEqual(config['environment'], 'staging')
                self.assertEqual(set(config['services']), {'identity', 'website', 'billing'})
                
                # Verify staging allows both HTTP and HTTPS
                origins = mock_settings.CORS_ALLOWED_ORIGINS
                self.assertIn('https://identity.staging.vfservices.viloforge.com', origins)
                self.assertIn('http://identity.staging.vfservices.viloforge.com', origins)


class TestCORSHeadersCustomization(CORSIntegrationTestCase):
    """Test customization of CORS headers."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_ALLOW_HEADERS=['accept', 'authorization', 'content-type', 'x-custom-header'],
        CORS_ALLOW_METHODS=['GET', 'POST', 'PUT', 'DELETE']
    )
    def test_cors_custom_headers_and_methods(self):
        """Test that custom CORS headers and methods are properly set."""
        response = self.make_cors_request(
            self.auth_url, 
            self.allowed_origin,
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS='x-custom-header,content-type'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check allowed methods
        allowed_methods = response.get('Access-Control-Allow-Methods', '')
        for method in ['GET', 'POST', 'PUT', 'DELETE']:
            self.assertIn(method, allowed_methods)
        
        # Check allowed headers
        allowed_headers = response.get('Access-Control-Allow-Headers', '').lower()
        for header in ['accept', 'authorization', 'content-type', 'x-custom-header']:
            self.assertIn(header.lower(), allowed_headers)
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
        CORS_PREFLIGHT_MAX_AGE=3600
    )
    def test_cors_preflight_max_age(self):
        """Test that preflight cache max age is properly set."""
        response = self.make_cors_request(self.auth_url, self.allowed_origin)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Access-Control-Max-Age'),
            '3600'
        )


class TestCORSErrorHandling(CORSIntegrationTestCase):
    """Test CORS error handling scenarios."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com']
    )
    def test_cors_missing_origin_header(self):
        """Test CORS behavior when Origin header is missing."""
        response = self.client.options(self.auth_url)
        
        # Should process request regardless of CORS
        self.assertIn(response.status_code, [200, 404])
        self.assertIsNone(response.get('Access-Control-Allow-Origin'))
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com']
    )
    def test_cors_empty_origin_header(self):
        """Test CORS behavior with empty Origin header."""
        response = self.make_cors_request(self.auth_url, '')
        
        # Should not set CORS headers for empty origin
        self.assertIsNone(response.get('Access-Control-Allow-Origin'))
    
    def test_cors_invalid_regex_handling(self):
        """Test that invalid regex patterns are handled gracefully."""
        # Skip this test as Django CORS headers doesn't handle invalid regex gracefully
        # Our validate_origin function does handle it, which is tested in unit tests
        self.skipTest("Django CORS middleware doesn't handle invalid regex gracefully")


class TestCORSRealWorldScenarios(CORSIntegrationTestCase):
    """Test real-world CORS scenarios."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=[
            'https://www.vfservices.viloforge.com',
            'http://localhost:3000'
        ],
        CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
    )
    def test_cors_frontend_to_api_communication(self):
        """Test typical frontend to API CORS communication."""
        # Simulate frontend application making API requests
        frontend_origins = [
            'https://www.vfservices.viloforge.com',  # Main website
            'https://api-docs.vfservices.viloforge.com',  # API documentation
            'http://localhost:3000',  # Local development
        ]
        
        for origin in frontend_origins:
            with self.subTest(origin=origin):
                # Test preflight request
                preflight_response = self.make_cors_request(
                    self.auth_url,
                    origin,
                    HTTP_ACCESS_CONTROL_REQUEST_METHOD='POST',
                    HTTP_ACCESS_CONTROL_REQUEST_HEADERS='content-type,authorization'
                )
                
                self.assertEqual(preflight_response.status_code, 200)
                self.assertEqual(
                    preflight_response.get('Access-Control-Allow-Origin'),
                    origin
                )
                
                # Test actual request
                actual_response = self.make_cors_request(
                    self.health_url,
                    origin,
                    method='GET'
                )
                
                self.assertEqual(
                    actual_response.get('Access-Control-Allow-Origin'),
                    origin
                )
    
    def test_cors_swagger_ui_integration(self):
        """Test CORS integration with Swagger UI documentation."""
        # Swagger UI typically makes requests from the documentation domain
        swagger_origins = [
            'https://identity.vfservices.viloforge.com',  # Same domain as API
            'https://api-docs.vfservices.viloforge.com',  # Separate docs domain
        ]
        
        with override_settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
        ):
            for origin in swagger_origins:
                with self.subTest(origin=origin):
                    response = self.make_cors_request(
                        '/api/',  # Use API root
                        origin,
                        HTTP_ACCESS_CONTROL_REQUEST_METHOD='GET'
                    )
                    
                    # Should allow Swagger UI to access API documentation
                    self.assertEqual(
                        response.get('Access-Control-Allow-Origin'),
                        origin
                    )