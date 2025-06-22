#!/usr/bin/env python
"""
Test script to verify logging configuration works properly.
This script can be run independently to test the logging setup.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

import logging
from webapp.logging_utils import webapp_logger, security_logger, performance_logger, user_logger

def test_logging_configuration():
    """Test that all loggers work correctly."""
    print("Testing Django website logging configuration...")
    
    # Test different logger types
    loggers_to_test = [
        ('root', logging.getLogger()),
        ('main', logging.getLogger('main')),
        ('main.views', logging.getLogger('main.views')),
        ('webapp', logging.getLogger('webapp')),
        ('webapp.views', logging.getLogger('webapp.views')),
        ('accounts', logging.getLogger('accounts')),
        ('accounts.views', logging.getLogger('accounts.views')),
        ('webapp.security', logging.getLogger('webapp.security')),
        ('webapp.performance', logging.getLogger('webapp.performance')),
        ('webapp.user_actions', logging.getLogger('webapp.user_actions')),
        ('webapp.middleware', logging.getLogger('webapp.middleware')),
    ]
    
    print(f"\nTesting {len(loggers_to_test)} loggers...")
    
    for logger_name, logger in loggers_to_test:
        print(f"\nTesting logger: {logger_name}")
        
        # Test different log levels
        logger.debug(f"DEBUG: Test message from {logger_name}")
        logger.info(f"INFO: Test message from {logger_name}")
        logger.warning(f"WARNING: Test message from {logger_name}")
        logger.error(f"ERROR: Test message from {logger_name}")
        
        # Test structured logging
        logger.info(
            f"Structured log from {logger_name}",
            extra={
                'logger_name': logger_name,
                'test_data': 'structured_logging_test',
                'test_number': 123,
                'test_bool': True,
            }
        )
    
    print("\nTesting custom webapp loggers...")
    
    # Test custom webapp loggers
    webapp_logger.info("Test message from webapp_logger", test_key="test_value")
    security_logger.warning("Test security event", event_type="test", severity="warning")
    performance_logger.debug("Test performance log", duration_ms=100, operation="test")
    user_logger.info("Test user action", user="test_user", action="test_action")
    
    print("\nTesting exception logging...")
    
    # Test exception logging
    try:
        raise ValueError("This is a test exception")
    except Exception as e:
        logging.getLogger('webapp').error("Test exception logging", exc_info=True)
    
    print("\nLogging configuration test completed!")
    print("\nCheck the following log files:")
    print("- /tmp/website.log (main log)")
    print("- /tmp/website_debug.log (debug log)")
    print("- /tmp/website_errors.log (error log)")
    print("- /tmp/website_performance.log (performance log)")
    print("- /tmp/website_security.log (security log)")

if __name__ == "__main__":
    test_logging_configuration()
