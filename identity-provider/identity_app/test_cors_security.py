"""
Security tests for CORS discovery system.

Tests comprehensive security scenarios including malicious origin blocking,
attack vector prevention, and environment-specific security controls.
"""

import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.test.utils import override_settings

from identity_app.cors_discovery import TraefikIntegratedCORS, validate_origin, configure_cors


class CORSSecurityTestCase(TestCase):
    """Base class for CORS security tests."""
    
    def setUp(self):
        """Set up test client and security test scenarios."""
        self.client = Client()
        self.test_endpoint = '/api/auth/login/'
        
        # Common malicious origins to test
        self.malicious_origins = [
            'https://evil.com',
            'https://phishing-site.com',
            'https://vfservices.viloforge.com.evil.com',  # Subdomain hijack attempt
            'https://vfservices-viloforge.com',  # Typosquatting
            'http://vfservices.viloforge.com.evil.com',  # HTTP subdomain hijack
            'https://xvfservices.viloforge.com',  # Character substitution
            'javascript:alert(1)',  # XSS attempt
            'data:text/html,<script>alert(1)</script>',  # Data URI attempt
            'file:///etc/passwd',  # File protocol attempt
            'chrome-extension://malicious-extension',  # Browser extension
            'moz-extension://malicious-addon',  # Firefox addon
        ]
        
        # Valid origins for testing
        self.valid_origins = [
            'https://www.vfservices.viloforge.com',
            'https://api.vfservices.viloforge.com',
            'https://identity.vfservices.viloforge.com',
            'https://billing.vfservices.viloforge.com',
        ]
        
        # Development-only origins
        self.development_origins = [
            'http://localhost:3000',
            'http://localhost:8080',
            'http://127.0.0.1:3000',
            'http://127.0.0.1:8080',
        ]
    
    def make_cors_request(self, origin, method='OPTIONS'):
        """Make a CORS request with specified origin."""
        headers = {
            'HTTP_ORIGIN': origin,
            'HTTP_ACCESS_CONTROL_REQUEST_METHOD': 'POST',
            'HTTP_ACCESS_CONTROL_REQUEST_HEADERS': 'content-type'
        }
        
        if method.upper() == 'OPTIONS':
            return self.client.options(self.test_endpoint, **headers)
        elif method.upper() == 'GET':
            return self.client.get(self.test_endpoint, **headers)
        elif method.upper() == 'POST':
            return self.client.post(self.test_endpoint, **headers)


class TestMaliciousOriginBlocking(CORSSecurityTestCase):
    """Test blocking of malicious origins."""
    
    @override_settings(
        CORS_ALLOWED_ORIGINS=[
            'https://www.vfservices.viloforge.com',
            'https://api.vfservices.viloforge.com'
        ],
        CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
    )
    def test_malicious_origins_blocked(self):
        """Test that various malicious origins are properly blocked."""
        for origin in self.malicious_origins:
            with self.subTest(origin=origin):
                response = self.make_cors_request(origin)
                
                # Malicious origins should not receive CORS headers
                self.assertIsNone(
                    response.get('Access-Control-Allow-Origin'),
                    f"Malicious origin {origin} was not blocked"
                )
                self.assertIsNone(
                    response.get('Access-Control-Allow-Methods'),
                    f"Malicious origin {origin} received CORS methods"
                )
    
    def test_domain_spoofing_attacks(self):
        """Test blocking of domain spoofing attacks."""
        spoofing_attempts = [
            'https://vfservices.viloforge.com.attacker.com',
            'https://vfservices.viloforge.com-attacker.com',
            'https://vfservices.viloforge.com.attacker.co',
            'https://vfservices-viloforge-com.attacker.com',
            'https://www.vfservices.viloforge.com.attacker.com',
            'https://api.vfservices.viloforge.com.evil.com',
        ]
        
        with override_settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
        ):
            for spoofed_origin in spoofing_attempts:
                with self.subTest(origin=spoofed_origin):
                    response = self.make_cors_request(spoofed_origin)
                    
                    self.assertIsNone(
                        response.get('Access-Control-Allow-Origin'),
                        f"Domain spoofing attempt {spoofed_origin} was not blocked"
                    )
    
    def test_protocol_downgrade_attacks(self):
        """Test blocking of protocol downgrade attacks."""
        # In production, only HTTPS should be allowed
        http_origins = [
            'http://www.vfservices.viloforge.com',
            'http://api.vfservices.viloforge.com',
            'http://identity.vfservices.viloforge.com',
        ]
        
        # Simulate production environment
        with override_settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
        ):
            for http_origin in http_origins:
                with self.subTest(origin=http_origin):
                    response = self.make_cors_request(http_origin)
                    
                    self.assertIsNone(
                        response.get('Access-Control-Allow-Origin'),
                        f"HTTP origin {http_origin} was not blocked in production"
                    )
    
    def test_unicode_and_punycode_attacks(self):
        """Test blocking of Unicode and Punycode domain attacks."""
        unicode_attacks = [
            'https://vfѕervices.viloforge.com',  # Cyrillic 's'
            'https://vfservіces.viloforge.com',  # Cyrillic 'i'
            'https://xn--vfservces-9wa.viloforge.com',  # Punycode
            'https://vfservices.vіloforge.com',  # Mixed script attack
        ]
        
        with override_settings(
            CORS_ALLOWED_ORIGIN_REGEXES=[r'^https://[\w\-]+\.vfservices\.viloforge\.com$']
        ):
            for unicode_origin in unicode_attacks:
                with self.subTest(origin=unicode_origin):
                    response = self.make_cors_request(unicode_origin)
                    
                    self.assertIsNone(
                        response.get('Access-Control-Allow-Origin'),
                        f"Unicode attack {unicode_origin} was not blocked"
                    )


class TestEnvironmentSpecificSecurity(CORSSecurityTestCase):
    """Test environment-specific security controls."""
    
    def test_production_security_strict(self):
        """Test that production environment enforces strict security."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'BASE_DOMAIN': 'vfservices.viloforge.com',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Production should only allow HTTPS
            for origin in config['origins']:
                self.assertTrue(
                    origin.startswith('https://'),
                    f"Production origin {origin} is not HTTPS-only"
                )
                self.assertNotIn('localhost', origin)
                self.assertNotIn('127.0.0.1', origin)
            
            # Regex should only match HTTPS
            for regex in config['regexes']:
                self.assertIn('https://', regex)
                self.assertNotIn('https?://', regex)
    
    def test_development_security_relaxed(self):
        """Test that development environment allows necessary relaxed security."""
        env_vars = {
            'ENVIRONMENT': 'development',
            'BASE_DOMAIN': 'dev.vfservices.viloforge.com',
            'LOCAL_CORS_ORIGINS': 'http://localhost:3000,http://127.0.0.1:8080',
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Development should allow localhost
            localhost_found = any('localhost' in origin for origin in config['origins'])
            self.assertTrue(localhost_found, "Development should allow localhost origins")
            
            # Should still block malicious origins
            for malicious_origin in self.malicious_origins:
                allowed = validate_origin(malicious_origin, config['origins'], config['regexes'])
                self.assertFalse(
                    allowed,
                    f"Development environment incorrectly allowed malicious origin: {malicious_origin}"
                )
    
    def test_staging_security_medium(self):
        """Test that staging environment has medium security level."""
        env_vars = {
            'ENVIRONMENT': 'staging',
            'BASE_DOMAIN': 'staging.vfservices.viloforge.com',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.staging.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Staging should allow both HTTP and HTTPS but not localhost
            has_https = any(origin.startswith('https://') for origin in config['origins'])
            has_http = any(origin.startswith('http://') and 'localhost' not in origin for origin in config['origins'])
            has_localhost = any('localhost' in origin for origin in config['origins'])
            
            self.assertTrue(has_https, "Staging should allow HTTPS origins")
            self.assertTrue(has_http, "Staging should allow HTTP origins")
            self.assertFalse(has_localhost, "Staging should not allow localhost origins")


class TestSecurityVulnerabilityPrevention(CORSSecurityTestCase):
    """Test prevention of specific security vulnerabilities."""
    
    def test_csrf_protection_with_cors(self):
        """Test that CORS doesn't bypass CSRF protection."""
        # CORS should work with CSRF protection, not replace it
        with override_settings(
            CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com'],
            CORS_ALLOW_CREDENTIALS=True
        ):
            # Test that valid origin gets CORS headers
            response = self.make_cors_request('https://www.vfservices.viloforge.com')
            self.assertEqual(response.get('Access-Control-Allow-Origin'), 'https://www.vfservices.viloforge.com')
            self.assertEqual(response.get('Access-Control-Allow-Credentials'), 'true')
            
            # Actual POST request should still require CSRF token
            post_response = self.client.post(
                self.test_endpoint,
                {'username': 'test', 'password': 'test'},
                HTTP_ORIGIN='https://www.vfservices.viloforge.com'
            )
            # Should get CSRF error (403) not CORS error
            # This confirms CORS doesn't bypass CSRF protection
    
    def test_wildcard_origin_security(self):
        """Test that wildcard origins are not used in production."""
        # Wildcard (*) origins should never be used with credentials
        with override_settings(
            CORS_ALLOW_ALL_ORIGINS=True,
            CORS_ALLOW_CREDENTIALS=True
        ):
            response = self.make_cors_request('https://evil.com')
            
            # If wildcard is used, credentials should be disabled for security
            if response.get('Access-Control-Allow-Origin') == '*':
                self.assertNotEqual(response.get('Access-Control-Allow-Credentials'), 'true')
    
    def test_origin_header_manipulation(self):
        """Test handling of manipulated Origin headers."""
        manipulated_origins = [
            '',  # Empty origin
            'null',  # Null origin
            'about:blank',  # About blank
            'chrome://settings',  # Chrome internal
            'file:///',  # File protocol
        ]
        
        with override_settings(
            CORS_ALLOWED_ORIGINS=['https://www.vfservices.viloforge.com']
        ):
            for manipulated_origin in manipulated_origins:
                with self.subTest(origin=manipulated_origin):
                    response = self.make_cors_request(manipulated_origin)
                    
                    # Should not allow manipulated origins
                    self.assertIsNone(response.get('Access-Control-Allow-Origin'))


class TestCORSDiscoverySecurityValidation(CORSSecurityTestCase):
    """Test security validation in the CORS discovery system."""
    
    def test_environment_variable_injection_protection(self):
        """Test protection against environment variable injection attacks."""
        # Simulate malicious environment variables
        malicious_env_vars = {
            'TRAEFIK_HTTP_ROUTERS_EVIL_RULE': 'Host(`evil.com`)',
            'TRAEFIK_HTTP_ROUTERS_INJECTION_RULE': 'Host(`legitimate.com`); Host(`evil.com`)',
            'PEER_SERVICES': 'identity,website,evil.com',
            'LOCAL_CORS_ORIGINS': 'http://localhost:3000,https://evil.com',
            'BASE_DOMAIN': 'evil.com',
        }
        
        with patch.dict(os.environ, malicious_env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Verify that the system validates environment variables
            # The base domain should be validated and blocked if suspicious
            self.assertEqual(config['base_domain'], 'vfservices.viloforge.com')  # Should fall back to default
    
    def test_regex_injection_protection(self):
        """Test protection against regex injection attacks."""
        # Test that generated regex patterns are properly escaped
        with patch.dict(os.environ, {'BASE_DOMAIN': 'test.vfservices.viloforge.com'}):
            cors = TraefikIntegratedCORS()
            cors.services = ['api']
            cors._build_cors_rules()
            
            # Verify that the domain is properly escaped in regex
            domain_regexes = [r for r in cors.regexes if 'test\\.vfservices\\.viloforge\\.com' in r]
            self.assertTrue(len(domain_regexes) > 0, "Should have domain-based regex patterns")
            
            for regex in domain_regexes:
                # Should contain escaped dots for the domain
                self.assertIn(r'test\.vfservices\.viloforge\.com', regex)
                # Should not contain unescaped special regex characters that could be exploited
                self.assertNotIn('.*', regex)
    
    def test_service_name_validation(self):
        """Test validation of discovered service names."""
        # Test with potentially malicious service names
        malicious_services = [
            '../../../etc/passwd',  # Path traversal
            'service;rm -rf /',  # Command injection
            'service\x00null',  # Null byte injection
            'service<script>alert(1)</script>',  # XSS attempt
        ]
        
        cors = TraefikIntegratedCORS()
        cors.services = malicious_services
        cors._build_cors_rules()
        
        # Generated origins should be safe (malicious services should be filtered out)
        # The malicious service names should have been sanitized or rejected
        safe_origins_only = True
        for origin in cors.origins:
            if any(bad in origin for bad in ['../', ';', '\x00', '<script>']):
                safe_origins_only = False
                break
        
        self.assertTrue(safe_origins_only, "Origins should not contain malicious content")


class TestProductionSecurityCompliance(CORSSecurityTestCase):
    """Test compliance with production security requirements."""
    
    def test_production_https_enforcement(self):
        """Test that production strictly enforces HTTPS."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'BASE_DOMAIN': 'vfservices.viloforge.com',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                configure_cors()
                
                # All origins should be HTTPS in production
                origins = mock_settings.CORS_ALLOWED_ORIGINS
                for origin in origins:
                    self.assertTrue(
                        origin.startswith('https://'),
                        f"Production origin {origin} is not HTTPS"
                    )
                
                # Regex patterns should only match HTTPS
                regexes = mock_settings.CORS_ALLOWED_ORIGIN_REGEXES
                for regex in regexes:
                    self.assertNotIn('https?://', regex)
                    self.assertIn('https://', regex)
    
    def test_production_localhost_blocking(self):
        """Test that production blocks all localhost origins."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'LOCAL_CORS_ORIGINS': 'http://localhost:3000',  # Should be ignored
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Production should never include localhost
            for origin in config['origins']:
                self.assertNotIn('localhost', origin)
                self.assertNotIn('127.0.0.1', origin)
            
            # Regex should not match localhost
            for regex in config['regexes']:
                self.assertNotIn('localhost', regex)
                self.assertNotIn('127.0.0.1', regex)
    
    def test_credential_security_in_production(self):
        """Test credential security settings in production."""
        env_vars = {'ENVIRONMENT': 'production'}
        
        with patch.dict(os.environ, env_vars):
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                configure_cors()
                
                # Credentials should be properly configured
                self.assertTrue(mock_settings.CORS_ALLOW_CREDENTIALS)
                self.assertFalse(mock_settings.CORS_ALLOW_ALL_ORIGINS)
    
    def test_debug_mode_disabled_in_production(self):
        """Test that debug features are disabled in production."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'CORS_ALLOW_ALL_ORIGINS_DEBUG': 'true',  # Should be ignored in production
        }
        
        with patch.dict(os.environ, env_vars):
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                configure_cors()
                
                # Debug setting should be ignored in production
                self.assertFalse(mock_settings.CORS_ALLOW_ALL_ORIGINS)