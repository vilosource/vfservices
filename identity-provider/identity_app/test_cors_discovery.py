"""
Comprehensive unit tests for the CORS discovery system.

Tests cover environment detection, service discovery, CORS rule generation,
and security validation across different deployment scenarios.
"""

import os
import pytest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.test.utils import override_settings

from identity_app.cors_discovery import TraefikIntegratedCORS, configure_cors, validate_origin


class TestTraefikIntegratedCORS(TestCase):
    """Test the TraefikIntegratedCORS class functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.cors = TraefikIntegratedCORS()
    
    def test_environment_detection_explicit_production(self):
        """Test environment detection with explicit ENVIRONMENT=production."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            cors = TraefikIntegratedCORS()
            self.assertEqual(cors.environment, 'production')
    
    def test_environment_detection_explicit_staging(self):
        """Test environment detection with explicit ENVIRONMENT=staging."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
            cors = TraefikIntegratedCORS()
            self.assertEqual(cors.environment, 'staging')
    
    def test_environment_detection_explicit_development(self):
        """Test environment detection with explicit ENVIRONMENT=development."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            cors = TraefikIntegratedCORS()
            self.assertEqual(cors.environment, 'development')
    
    def test_environment_detection_invalid_value(self):
        """Test environment detection with invalid ENVIRONMENT value falls back to DEBUG."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'invalid'}):
            with patch('django.conf.settings.DEBUG', True):
                cors = TraefikIntegratedCORS()
                self.assertEqual(cors.environment, 'development')
    
    def test_environment_detection_debug_fallback(self):
        """Test environment detection falling back to DEBUG setting."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('django.conf.settings.DEBUG', True):
                cors = TraefikIntegratedCORS()
                self.assertEqual(cors.environment, 'development')
    
    def test_environment_detection_default_fallback(self):
        """Test environment detection with no environment variables or DEBUG setting."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('django.conf.settings.DEBUG', False):
                cors = TraefikIntegratedCORS()
                self.assertEqual(cors.environment, 'development')
    
    def test_base_domain_default(self):
        """Test default base domain configuration."""
        with patch.dict(os.environ, {}, clear=True):
            cors = TraefikIntegratedCORS()
            self.assertEqual(cors.base_domain, 'vfservices.viloforge.com')
    
    def test_base_domain_custom(self):
        """Test custom base domain configuration."""
        with patch.dict(os.environ, {'BASE_DOMAIN': 'test.vfservices.viloforge.com'}):
            cors = TraefikIntegratedCORS()
            self.assertEqual(cors.base_domain, 'test.vfservices.viloforge.com')


class TestTraefikDiscovery(TestCase):
    """Test Traefik environment variable discovery."""
    
    def test_traefik_discovery_success(self):
        """Test successful Traefik variable discovery."""
        env_vars = {
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
            'TRAEFIK_HTTP_ROUTERS_WEBSITE_RULE': 'Host(`www.vfservices.viloforge.com`)',
            'TRAEFIK_HTTP_ROUTERS_API_RULE': 'Host(`api.vfservices.viloforge.com`)',
            'BASE_DOMAIN': 'vfservices.viloforge.com'
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            result = cors._discover_from_traefik_env()
            
            self.assertTrue(result)
            self.assertIn('identity', cors.services)
            self.assertIn('website', cors.services)
            self.assertIn('api', cors.services)
            self.assertEqual(len(cors.services), 3)
    
    def test_traefik_discovery_no_variables(self):
        """Test Traefik discovery with no environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            cors = TraefikIntegratedCORS()
            result = cors._discover_from_traefik_env()
            
            self.assertFalse(result)
            self.assertEqual(len(cors.services), 0)
    
    def test_traefik_discovery_invalid_format(self):
        """Test Traefik discovery with invalid variable format."""
        env_vars = {
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Invalid rule format',
            'TRAEFIK_HTTP_ROUTERS_WEBSITE_RULE': 'PathPrefix(`/api`)',  # No Host rule
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            result = cors._discover_from_traefik_env()
            
            # Should still return False since no valid Host rules found
            self.assertFalse(result)
    
    def test_traefik_discovery_partial_success(self):
        """Test Traefik discovery with some valid and some invalid variables."""
        env_vars = {
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
            'TRAEFIK_HTTP_ROUTERS_INVALID_RULE': 'Invalid rule format',
            'TRAEFIK_HTTP_ROUTERS_WEBSITE_RULE': 'Host(`www.vfservices.viloforge.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            result = cors._discover_from_traefik_env()
            
            self.assertTrue(result)
            self.assertIn('identity', cors.services)
            self.assertIn('website', cors.services)
            self.assertEqual(len(cors.services), 2)


class TestFallbackConfiguration(TestCase):
    """Test fallback configuration mechanisms."""
    
    def test_fallback_with_peer_services(self):
        """Test fallback configuration with PEER_SERVICES environment variable."""
        with patch.dict(os.environ, {'PEER_SERVICES': 'identity,website,billing,inventory'}):
            cors = TraefikIntegratedCORS()
            cors._use_fallback_config()
            
            expected_services = ['identity', 'website', 'billing', 'inventory']
            self.assertEqual(cors.services, expected_services)
    
    def test_fallback_with_peer_services_whitespace(self):
        """Test fallback configuration with PEER_SERVICES containing whitespace."""
        with patch.dict(os.environ, {'PEER_SERVICES': ' identity , website , billing , inventory '}):
            cors = TraefikIntegratedCORS()
            cors._use_fallback_config()
            
            expected_services = ['identity', 'website', 'billing', 'inventory']
            self.assertEqual(cors.services, expected_services)
    
    def test_fallback_default_services(self):
        """Test fallback configuration with default services."""
        with patch.dict(os.environ, {}, clear=True):
            cors = TraefikIntegratedCORS()
            cors._use_fallback_config()
            
            expected_services = ['identity', 'website', 'billing', 'inventory']
            self.assertEqual(cors.services, expected_services)
    
    def test_fallback_empty_peer_services(self):
        """Test fallback configuration with empty PEER_SERVICES."""
        with patch.dict(os.environ, {'PEER_SERVICES': ''}):
            cors = TraefikIntegratedCORS()
            cors._use_fallback_config()
            
            expected_services = ['identity', 'website', 'billing', 'inventory']
            self.assertEqual(cors.services, expected_services)


class TestCORSRuleGeneration(TestCase):
    """Test CORS rule generation for different environments."""
    
    def test_cors_rules_production(self):
        """Test CORS rule generation for production environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'BASE_DOMAIN': 'vfservices.viloforge.com'}):
            cors = TraefikIntegratedCORS()
            cors.services = ['identity', 'website']
            cors._build_cors_rules()
            
            # Should only include HTTPS origins
            self.assertIn('https://identity.vfservices.viloforge.com', cors.origins)
            self.assertIn('https://website.vfservices.viloforge.com', cors.origins)
            self.assertNotIn('http://identity.vfservices.viloforge.com', cors.origins)
            self.assertNotIn('http://localhost:3000', cors.origins)
            
            # Should include HTTPS-only regex
            self.assertEqual(len(cors.regexes), 1)
            self.assertIn(r'^https://[\w\-]+\.vfservices\.viloforge\.com$', cors.regexes)
    
    def test_cors_rules_staging(self):
        """Test CORS rule generation for staging environment."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'staging', 'BASE_DOMAIN': 'staging.vfservices.viloforge.com'}):
            cors = TraefikIntegratedCORS()
            cors.services = ['identity', 'api']
            cors._build_cors_rules()
            
            # Should include both HTTP and HTTPS origins
            self.assertIn('https://identity.staging.vfservices.viloforge.com', cors.origins)
            self.assertIn('http://identity.staging.vfservices.viloforge.com', cors.origins)
            self.assertIn('https://api.staging.vfservices.viloforge.com', cors.origins)
            self.assertIn('http://api.staging.vfservices.viloforge.com', cors.origins)
            
            # Should not include localhost
            self.assertNotIn('http://localhost:3000', cors.origins)
            
            # Should include HTTP/HTTPS regex
            self.assertEqual(len(cors.regexes), 1)
            self.assertIn(r'^https?://[\w\-]+\.staging\.vfservices\.viloforge\.com$', cors.regexes)
    
    def test_cors_rules_development(self):
        """Test CORS rule generation for development environment."""
        env_vars = {
            'ENVIRONMENT': 'development',
            'BASE_DOMAIN': 'dev.vfservices.viloforge.com',
            'LOCAL_CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000'
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            cors.services = ['identity']
            cors._build_cors_rules()
            
            # Should include both HTTP and HTTPS origins
            self.assertIn('https://identity.dev.vfservices.viloforge.com', cors.origins)
            self.assertIn('http://identity.dev.vfservices.viloforge.com', cors.origins)
            
            # Should include localhost origins
            self.assertIn('http://localhost:3000', cors.origins)
            self.assertIn('http://localhost:8080', cors.origins)
            self.assertIn('http://127.0.0.1:3000', cors.origins)
            
            # Should include domain and localhost regexes
            self.assertEqual(len(cors.regexes), 3)
            self.assertIn(r'^https?://[\w\-]+\.dev\.vfservices\.viloforge\.com$', cors.regexes)
            self.assertIn(r'^https?://localhost:\d+$', cors.regexes)
            self.assertIn(r'^https?://127\.0\.0\.1:\d+$', cors.regexes)
    
    def test_cors_rules_development_default_localhost(self):
        """Test CORS rule generation for development with default localhost origins."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}, clear=True):
            cors = TraefikIntegratedCORS()
            cors.services = ['identity']
            cors._build_cors_rules()
            
            # Should include default localhost origins
            self.assertIn('http://localhost:3000', cors.origins)
            self.assertIn('http://localhost:8080', cors.origins)
    
    def test_cors_rules_duplicate_removal(self):
        """Test that duplicate origins and regexes are removed."""
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            cors = TraefikIntegratedCORS()
            cors.services = ['identity', 'identity']  # Duplicate service
            cors._build_cors_rules()
            
            # Should not have duplicate origins
            origins = cors.origins
            self.assertEqual(len(origins), len(set(origins)))
            
            # Should not have duplicate regexes
            regexes = cors.regexes
            self.assertEqual(len(regexes), len(set(regexes)))


class TestOriginValidation(TestCase):
    """Test origin validation functionality."""
    
    def test_validate_origin_explicit_match(self):
        """Test origin validation with explicit origin match."""
        allowed_origins = ['https://example.com', 'http://localhost:3000']
        allowed_regexes = []
        
        self.assertTrue(validate_origin('https://example.com', allowed_origins, allowed_regexes))
        self.assertTrue(validate_origin('http://localhost:3000', allowed_origins, allowed_regexes))
        self.assertFalse(validate_origin('https://evil.com', allowed_origins, allowed_regexes))
    
    def test_validate_origin_regex_match(self):
        """Test origin validation with regex pattern match."""
        allowed_origins = []
        allowed_regexes = [r'^https://[\w\-]+\.example\.com$', r'^https?://localhost:\d+$']
        
        self.assertTrue(validate_origin('https://api.example.com', allowed_origins, allowed_regexes))
        self.assertTrue(validate_origin('https://sub-domain.example.com', allowed_origins, allowed_regexes))
        self.assertTrue(validate_origin('http://localhost:8000', allowed_origins, allowed_regexes))
        self.assertTrue(validate_origin('https://localhost:3000', allowed_origins, allowed_regexes))
        
        # Should reject non-matching origins
        self.assertFalse(validate_origin('https://evil.com', allowed_origins, allowed_regexes))
        self.assertFalse(validate_origin('http://example.com.evil.com', allowed_origins, allowed_regexes))
    
    def test_validate_origin_invalid_regex(self):
        """Test origin validation with invalid regex pattern."""
        allowed_origins = []
        allowed_regexes = [r'[invalid regex', r'^https://valid\.com$']
        
        # Should still work with valid regex despite invalid one
        self.assertTrue(validate_origin('https://valid.com', allowed_origins, allowed_regexes))
        self.assertFalse(validate_origin('https://invalid.com', allowed_origins, allowed_regexes))


class TestConfigureCORS(TestCase):
    """Test the configure_cors function."""
    
    @patch('identity_app.cors_discovery.TraefikIntegratedCORS')
    def test_configure_cors_success(self, mock_cors_class):
        """Test successful CORS configuration."""
        # Mock the CORS discovery
        mock_instance = Mock()
        mock_instance.discover_configuration.return_value = {
            'origins': ['https://example.com'],
            'regexes': [r'^https://[\w\-]+\.example\.com$'],
            'environment': 'production',
            'base_domain': 'example.com',
            'services': ['identity']
        }
        mock_cors_class.return_value = mock_instance
        
        # Mock settings
        with patch('identity_app.cors_discovery.settings') as mock_settings:
            result = configure_cors()
            
            # Verify settings were updated
            self.assertEqual(mock_settings.CORS_ALLOWED_ORIGINS, ['https://example.com'])
            self.assertEqual(mock_settings.CORS_ALLOWED_ORIGIN_REGEXES, [r'^https://[\w\-]+\.example\.com$'])
            self.assertTrue(mock_settings.CORS_ALLOW_CREDENTIALS)
            self.assertFalse(mock_settings.CORS_ALLOW_ALL_ORIGINS)
            
            # Verify result
            self.assertIsNotNone(result)
            self.assertEqual(result['environment'], 'production')
    
    @patch('identity_app.cors_discovery.TraefikIntegratedCORS')
    def test_configure_cors_development_debug_mode(self, mock_cors_class):
        """Test CORS configuration in development with debug mode."""
        # Mock the CORS discovery
        mock_instance = Mock()
        mock_instance.discover_configuration.return_value = {
            'origins': ['http://localhost:3000'],
            'regexes': [r'^https?://localhost:\d+$'],
            'environment': 'development',
            'base_domain': 'example.com',
            'services': ['identity']
        }
        mock_cors_class.return_value = mock_instance
        
        with patch.dict(os.environ, {'CORS_ALLOW_ALL_ORIGINS_DEBUG': 'true'}):
            with patch('identity_app.cors_discovery.settings') as mock_settings:
                result = configure_cors()
                
                # Verify debug settings were applied
                self.assertTrue(mock_settings.CORS_ALLOW_ALL_ORIGINS)
    
    @patch('identity_app.cors_discovery.TraefikIntegratedCORS')
    def test_configure_cors_exception_handling(self, mock_cors_class):
        """Test CORS configuration with exception handling."""
        # Mock an exception
        mock_cors_class.side_effect = Exception("Discovery failed")
        
        result = configure_cors()
        
        # Should return None on exception
        self.assertIsNone(result)


class TestDiscoveryIntegration(TestCase):
    """Test the complete discovery flow integration."""
    
    def test_complete_discovery_flow_traefik_success(self):
        """Test complete discovery flow with successful Traefik discovery."""
        env_vars = {
            'ENVIRONMENT': 'staging',
            'BASE_DOMAIN': 'test.example.com',
            'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.test.example.com`)',
            'TRAEFIK_HTTP_ROUTERS_API_RULE': 'Host(`api.test.example.com`)',
        }
        
        with patch.dict(os.environ, env_vars):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Verify configuration
            self.assertEqual(config['environment'], 'staging')
            self.assertEqual(config['base_domain'], 'test.example.com')
            self.assertEqual(set(config['services']), {'identity', 'api'})
            
            # Verify origins include both HTTP and HTTPS for staging
            origins = config['origins']
            self.assertIn('https://identity.test.example.com', origins)
            self.assertIn('http://identity.test.example.com', origins)
            self.assertIn('https://api.test.example.com', origins)
            self.assertIn('http://api.test.example.com', origins)
            
            # Verify regex patterns
            regexes = config['regexes']
            self.assertEqual(len(regexes), 1)
            self.assertIn(r'^https?://[\w\-]+\.test\.example\.com$', regexes)
    
    def test_complete_discovery_flow_fallback(self):
        """Test complete discovery flow falling back to default configuration."""
        env_vars = {
            'ENVIRONMENT': 'production',
            'BASE_DOMAIN': 'vfservices.viloforge.com',
            'PEER_SERVICES': 'identity,website,billing'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            cors = TraefikIntegratedCORS()
            config = cors.discover_configuration()
            
            # Verify fallback configuration
            self.assertEqual(config['environment'], 'production')
            self.assertEqual(config['base_domain'], 'vfservices.viloforge.com')
            self.assertEqual(set(config['services']), {'identity', 'website', 'billing'})
            
            # Verify production HTTPS-only origins
            origins = config['origins']
            self.assertIn('https://identity.vfservices.viloforge.com', origins)
            self.assertIn('https://website.vfservices.viloforge.com', origins)
            self.assertIn('https://billing.vfservices.viloforge.com', origins)
            
            # Should not include HTTP origins in production
            self.assertNotIn('http://identity.vfservices.viloforge.com', origins)
            self.assertNotIn('http://localhost:3000', origins)


if __name__ == '__main__':
    pytest.main([__file__])