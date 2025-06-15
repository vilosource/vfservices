#!/usr/bin/env python
"""
Demo script for the CORS Discovery System.

This script demonstrates how the Traefik-Integrated CORS Discovery System works
in different environments with various configurations.
"""

import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.test_settings')
django.setup()

from identity_app.cors_discovery import TraefikIntegratedCORS, configure_cors


def demo_environment(env_name, env_vars):
    """Demonstrate CORS discovery for a specific environment."""
    print(f"\n{'='*60}")
    print(f"CORS Discovery Demo - {env_name.upper()} Environment")
    print(f"{'='*60}")
    
    # Clear and set environment variables
    for key in list(os.environ.keys()):
        if key.startswith(('ENVIRONMENT', 'BASE_DOMAIN', 'TRAEFIK_', 'PEER_SERVICES', 'LOCAL_CORS_ORIGINS')):
            del os.environ[key]
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"  {key} = {value}")
    
    print("\nDiscovering CORS configuration...")
    
    # Run discovery
    cors = TraefikIntegratedCORS()
    config = cors.discover_configuration()
    
    print(f"\nDiscovery Results:")
    print(f"  Environment: {config['environment']}")
    print(f"  Base Domain: {config['base_domain']}")
    print(f"  Services: {config['services']}")
    print(f"  Origins ({len(config['origins'])}):")
    for origin in config['origins']:
        print(f"    - {origin}")
    print(f"  Regex Patterns ({len(config['regexes'])}):")
    for regex in config['regexes']:
        print(f"    - {regex}")


def main():
    """Run CORS discovery demos."""
    print("Traefik-Integrated CORS Discovery System Demo")
    print("=" * 60)
    
    # Production environment with Traefik discovery
    demo_environment("Production", {
        'ENVIRONMENT': 'production',
        'BASE_DOMAIN': 'vfservices.viloforge.com',
        'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.vfservices.viloforge.com`)',
        'TRAEFIK_HTTP_ROUTERS_WEBSITE_RULE': 'Host(`www.vfservices.viloforge.com`)',
        'TRAEFIK_HTTP_ROUTERS_BILLING_RULE': 'Host(`billing.vfservices.viloforge.com`)',
    })
    
    # Staging environment with fallback
    demo_environment("Staging", {
        'ENVIRONMENT': 'staging',
        'BASE_DOMAIN': 'staging.vfservices.viloforge.com',
        'PEER_SERVICES': 'identity,website,billing,inventory',
    })
    
    # Development environment with localhost
    demo_environment("Development", {
        'ENVIRONMENT': 'development',
        'BASE_DOMAIN': 'dev.vfservices.viloforge.com',
        'LOCAL_CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080,http://127.0.0.1:3000',
        'TRAEFIK_HTTP_ROUTERS_IDENTITY_RULE': 'Host(`identity.dev.vfservices.viloforge.com`)',
    })
    
    # Security demo - malicious inputs blocked
    demo_environment("Security Test", {
        'ENVIRONMENT': 'production',
        'BASE_DOMAIN': 'evil.com',  # This will be blocked
        'PEER_SERVICES': 'identity,../../../etc/passwd,service;rm -rf /,normal-service',
    })
    
    print(f"\n{'='*60}")
    print("Demo completed! The CORS discovery system:")
    print("✅ Automatically detects services from Traefik configuration")
    print("✅ Applies environment-specific security levels")
    print("✅ Blocks malicious inputs and validates domains")
    print("✅ Falls back gracefully when discovery fails")
    print("✅ Supports development with localhost origins")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()