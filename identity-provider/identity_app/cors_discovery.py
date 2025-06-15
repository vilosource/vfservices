"""
Traefik-Integrated CORS Discovery System for the VF Services Identity Provider.

This module automatically configures Cross-Origin Resource Sharing (CORS) policies
based on the deployment environment and service discovery through Traefik reverse
proxy integration.
"""

import os
import re
import logging
from typing import List, Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class TraefikIntegratedCORS:
    """
    Traefik-integrated CORS discovery system for automatic origin configuration.
    
    This class automatically discovers services and their origins from Traefik
    configuration and applies appropriate CORS policies based on the environment.
    """
    
    def __init__(self):
        self.base_domain = self._validate_base_domain(os.getenv('BASE_DOMAIN', 'vfservices.viloforge.com'))
        self.environment = self._detect_environment()
        self.services = []
        self.origins = []
        self.regexes = []
        
    def _detect_environment(self) -> str:
        """Detect the current environment with fallback logic."""
        # Priority 1: Explicit ENVIRONMENT variable
        env = os.getenv('ENVIRONMENT', '').lower()
        if env in ['production', 'staging', 'development']:
            logger.info(f"Environment detected from ENVIRONMENT variable: {env}")
            return env
            
        # Priority 2: Django DEBUG setting
        if getattr(settings, 'DEBUG', False):
            logger.info("Environment detected from DEBUG setting: development")
            return 'development'
            
        # Priority 3: Default to development
        logger.info("Environment defaulted to: development")
        return 'development'
    
    def _validate_base_domain(self, domain: str) -> str:
        """Validate and sanitize the base domain."""
        # Only allow known safe domains or default
        safe_domains = [
            'vfservices.viloforge.com',
            'staging.vfservices.viloforge.com',
            'dev.vfservices.viloforge.com',
            'test.vfservices.viloforge.com',
            'test.example.com'  # For testing
        ]
        
        if domain in safe_domains:
            return domain
        
        # For development/testing, allow localhost-like domains
        if 'localhost' in domain or '127.0.0.1' in domain or domain.endswith('.local'):
            return domain
            
        # Log suspicious domain and fall back to default
        logger.warning(f"Suspicious BASE_DOMAIN '{domain}' blocked, using default")
        return 'vfservices.viloforge.com'
    
    def _validate_service_name(self, service_name: str) -> str:
        """Validate and sanitize service names."""
        # Remove any path traversal attempts
        sanitized = service_name.replace('/', '').replace('\\', '').replace('..', '')
        
        # Remove special characters that could be used for injection
        sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', sanitized)
        
        # Ensure it's not empty after sanitization
        if not sanitized:
            logger.warning(f"Service name '{service_name}' sanitized to empty string, skipping")
            return None
            
        if sanitized != service_name:
            logger.warning(f"Service name '{service_name}' sanitized to '{sanitized}'")
            
        return sanitized
    
    def discover_configuration(self) -> Dict:
        """
        Main discovery method that tries multiple strategies.
        
        Returns:
            Dict: Configuration dictionary with origins and regexes
        """
        logger.info(f"Starting CORS discovery for environment: {self.environment}")
        
        # Try discovery methods in order of preference
        if self._discover_from_traefik_env():
            logger.info("Successfully discovered configuration from Traefik environment variables")
        elif self._discover_from_service_labels():
            logger.info("Successfully discovered configuration from service labels")
        else:
            logger.warning("Using fallback configuration - no automatic discovery succeeded")
            self._use_fallback_config()
        
        self._build_cors_rules()
        
        config = {
            'origins': self.origins,
            'regexes': self.regexes,
            'environment': self.environment,
            'base_domain': self.base_domain,
            'services': self.services
        }
        
        logger.info(f"CORS discovery completed. Found {len(self.services)} services, "
                   f"{len(self.origins)} origins, {len(self.regexes)} regex patterns")
        logger.debug(f"Services: {self.services}")
        logger.debug(f"Origins: {self.origins}")
        logger.debug(f"Regexes: {self.regexes}")
        
        return config
    
    def _discover_from_traefik_env(self) -> bool:
        """
        Discover services from Traefik environment variables.
        
        Looks for variables like:
        TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE=Host(`identity.vfservices.viloforge.com`)
        """
        traefik_vars = {k: v for k, v in os.environ.items() 
                       if k.startswith('TRAEFIK_HTTP_ROUTERS_') and k.endswith('_RULE')}
        
        if not traefik_vars:
            logger.debug("No Traefik environment variables found")
            return False
        
        logger.debug(f"Found {len(traefik_vars)} Traefik environment variables")
        
        services = []
        for var_name, rule in traefik_vars.items():
            # Extract service name from variable name
            # TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE -> identity
            parts = var_name.split('_')
            if len(parts) >= 4:
                raw_service_name = parts[3].lower()
                service_name = self._validate_service_name(raw_service_name)
                
                if service_name:  # Only proceed if validation passed
                    # Extract domain from Host() rule
                    host_match = re.search(r'Host\(`([^`]+)`\)', rule)
                    if host_match:
                        domain = host_match.group(1)
                        services.append(service_name)
                        logger.debug(f"Discovered service: {service_name} -> {domain}")
                    else:
                        logger.warning(f"Could not parse Host rule from {var_name}: {rule}")
        
        if services:
            self.services = services
            logger.info(f"Traefik discovery found {len(services)} services: {services}")
            return True
        
        logger.debug("No services found in Traefik environment variables")
        return False
    
    def _discover_from_service_labels(self) -> bool:
        """
        Discover services from Docker service labels (fallback method).
        
        This is a placeholder for future implementation that would query
        Docker API or use service discovery mechanisms.
        """
        # For now, return False to use fallback config
        # Future implementation could use Docker API to discover services
        logger.debug("Service label discovery not yet implemented")
        return False
    
    def _use_fallback_config(self):
        """Use fallback configuration when discovery fails."""
        # Check for manually configured peer services
        peer_services = os.getenv('PEER_SERVICES', '')
        if peer_services:
            raw_services = [s.strip() for s in peer_services.split(',') if s.strip()]
            validated_services = []
            for service in raw_services:
                validated = self._validate_service_name(service)
                if validated:
                    validated_services.append(validated)
            self.services = validated_services
            logger.info(f"Using PEER_SERVICES configuration: {self.services}")
        else:
            # Default services based on VF Services architecture
            self.services = ['identity', 'website', 'billing', 'inventory']
            logger.info(f"Using default service configuration: {self.services}")
    
    def _build_cors_rules(self):
        """Build CORS origins and regex patterns based on discovered services."""
        # Clear existing rules
        self.origins = []
        self.regexes = []
        
        # Sanitize services list first
        sanitized_services = []
        for service in self.services:
            validated = self._validate_service_name(service)
            if validated:
                sanitized_services.append(validated)
        self.services = sanitized_services
        
        # Base patterns for discovered services
        for service in self.services:
            service_domain = f"{service}.{self.base_domain}"
            
            if self.environment == 'production':
                # Production: HTTPS only
                self.origins.append(f"https://{service_domain}")
            else:
                # Staging/Development: HTTP and HTTPS
                self.origins.extend([
                    f"https://{service_domain}",
                    f"http://{service_domain}"
                ])
        
        # Add wildcard patterns for subdomains
        escaped_domain = re.escape(self.base_domain)
        if self.environment == 'production':
            self.regexes.append(rf"^https://[\w\-]+\.{escaped_domain}$")
        else:
            self.regexes.append(rf"^https?://[\w\-]+\.{escaped_domain}$")
        
        # Development: Add localhost support
        if self.environment == 'development':
            local_origins = os.getenv('LOCAL_CORS_ORIGINS', 'http://localhost:3000,http://localhost:8080')
            if local_origins:
                local_list = [origin.strip() for origin in local_origins.split(',') if origin.strip()]
                self.origins.extend(local_list)
                logger.debug(f"Added development localhost origins: {local_list}")
            
            # Localhost regex patterns
            self.regexes.extend([
                r"^https?://localhost:\d+$",
                r"^https?://127\.0\.0\.1:\d+$"
            ])
        
        # Remove duplicates while preserving order
        self.origins = list(dict.fromkeys(self.origins))
        self.regexes = list(dict.fromkeys(self.regexes))
        
        logger.debug(f"Built {len(self.origins)} origins and {len(self.regexes)} regex patterns")


def configure_cors():
    """Configure Django CORS settings using the discovery system."""
    logger.info("Configuring CORS using Traefik-integrated discovery system")
    
    try:
        discovery = TraefikIntegratedCORS()
        config = discovery.discover_configuration()
        
        # Apply to Django settings
        settings.CORS_ALLOWED_ORIGINS = config['origins']
        settings.CORS_ALLOWED_ORIGIN_REGEXES = config['regexes']
        
        # Environment-specific settings
        if config['environment'] == 'development':
            settings.CORS_ALLOW_CREDENTIALS = True
            # Only allow all origins if explicitly enabled for debugging
            debug_allow_all = os.getenv('CORS_ALLOW_ALL_ORIGINS_DEBUG', 'false').lower() == 'true'
            if debug_allow_all:
                settings.CORS_ALLOW_ALL_ORIGINS = True
                logger.warning("CORS_ALLOW_ALL_ORIGINS enabled - this should only be used for debugging!")
        else:
            # Production/Staging: More restrictive settings
            settings.CORS_ALLOW_CREDENTIALS = True
            settings.CORS_ALLOW_ALL_ORIGINS = False
        
        # Additional CORS headers
        settings.CORS_ALLOW_HEADERS = [
            'accept',
            'accept-encoding',
            'authorization',
            'content-type',
            'dnt',
            'origin',
            'user-agent',
            'x-csrftoken',
            'x-requested-with',
        ]
        
        settings.CORS_ALLOW_METHODS = [
            'DELETE',
            'GET',
            'OPTIONS',
            'PATCH',
            'POST',
            'PUT',
        ]
        
        # Preflight cache time (in seconds)
        settings.CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours
        
        logger.info(f"CORS configured for {config['environment']} environment")
        logger.info(f"Allowed {len(config['origins'])} explicit origins")
        logger.info(f"Configured {len(config['regexes'])} regex patterns")
        logger.debug(f"Allowed origins: {config['origins']}")
        logger.debug(f"Regex patterns: {config['regexes']}")
        
        return config
        
    except Exception as e:
        logger.error(f"Failed to configure CORS: {e}")
        # Fall back to existing manual configuration
        logger.warning("Falling back to existing manual CORS configuration")
        return None


def validate_origin(origin: str, allowed_origins: List[str], allowed_regexes: List[str]) -> bool:
    """
    Validate if an origin is allowed based on the configured rules.
    
    Args:
        origin: The origin to validate
        allowed_origins: List of explicitly allowed origins
        allowed_regexes: List of regex patterns for allowed origins
    
    Returns:
        bool: True if origin is allowed, False otherwise
    """
    # Check explicit origins
    if origin in allowed_origins:
        return True
    
    # Check regex patterns
    for pattern in allowed_regexes:
        try:
            if re.match(pattern, origin):
                return True
        except re.error as e:
            logger.error(f"Invalid regex pattern '{pattern}': {e}")
            continue
    
    return False