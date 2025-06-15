"""
Management command to test logging configuration for identity-provider.
"""

from django.core.management.base import BaseCommand
import logging
import os
from identity_app.logging_utils import (
    log_security_event, 
    log_jwt_operation
)


class Command(BaseCommand):
    help = 'Test logging configuration and utilities for identity-provider'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            default='info',
            help='Logging level to test (default: info)'
        )
        parser.add_argument(
            '--all-loggers',
            action='store_true',
            help='Test all configured loggers'
        )

    def handle(self, *args, **options):
        level = options['level']
        test_all = options['all_loggers']

        self.stdout.write(
            self.style.SUCCESS('Testing identity-provider logging configuration...')
        )

        # Test standard Django logger
        logger = logging.getLogger('identity_app')
        self.stdout.write(f"Testing standard logger at {level} level...")
        
        getattr(logger, level)(f"Test {level} message from identity management command")
        
        # Test logging utility functions (simplified for management command)
        self.stdout.write("Testing logging utility functions...")
        
        # Test security event logging (without request parameter)
        log_security_event(
            event_type='test_command_execution',
            severity='INFO'
        )

        # Test JWT operation logging
        log_jwt_operation(
            operation='test_token_generation',
            username='test_user',
            token_data={'test': True}
        )

        if test_all:
            self.stdout.write("Testing all configured loggers...")
            
            # Test all loggers defined in settings
            loggers_to_test = [
                'identity_app.auth',
                'identity_app.security',
                'identity_app.performance',
                'identity_app.jwt',
                'django.request',
                'django.security'
            ]

            for logger_name in loggers_to_test:
                test_logger = logging.getLogger(logger_name)
                self.stdout.write(f"Testing logger: {logger_name}")
                getattr(test_logger, level)(
                    f"Test {level} message from {logger_name}"
                )

        # Test different log levels
        self.stdout.write("Testing all log levels...")
        test_logger = logging.getLogger('identity_app.test')
        
        test_logger.debug("DEBUG: This is a debug message")
        test_logger.info("INFO: This is an info message")
        test_logger.warning("WARNING: This is a warning message")
        test_logger.error("ERROR: This is an error message")
        test_logger.critical("CRITICAL: This is a critical message")

        # Test exception logging
        try:
            raise ValueError("Test exception for logging")
        except Exception:
            test_logger.exception("Exception caught during logging test")

        self.stdout.write(
            self.style.SUCCESS('Logging test completed! Check the following log files:')
        )
        log_base_dir = os.environ.get("LOG_BASE_DIR", "/tmp")
        self.stdout.write(f'- {log_base_dir}/identity_provider.log (general logs)')
        self.stdout.write(f'- {log_base_dir}/identity_provider_debug.log (debug logs)')
        self.stdout.write(f'- {log_base_dir}/identity_provider_errors.log (error logs)')
        self.stdout.write(f'- {log_base_dir}/identity_provider_auth.log (authentication logs)')
        self.stdout.write(f'- {log_base_dir}/identity_provider_security.log (security logs)')
        self.stdout.write('- Console output should also show logs')
