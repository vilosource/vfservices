"""
Management command to test logging configuration for inventory-api.
"""

from django.core.management.base import BaseCommand
import logging
import os
from inventory.logging_utils import (
    log_inventory_operation, 
    log_security_event, 
    log_performance_metric
)


class Command(BaseCommand):
    help = 'Test logging configuration and utilities for inventory-api'

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
            self.style.SUCCESS('Testing inventory-api logging configuration...')
        )

        # Test standard Django logger
        logger = logging.getLogger('inventory')
        self.stdout.write(f"Testing standard logger at {level} level...")
        
        getattr(logger, level)(f"Test {level} message from inventory management command")
        
        # Test logging utility functions
        self.stdout.write("Testing logging utility functions...")
        
        # Test inventory operation logging
        log_inventory_operation(
            operation_type='test_inventory_check',
            item_id='test_item_123',
            quantity=10,
            extra_data={'test': True}
        )

        # Test security event logging
        log_security_event(
            event_type='test_command_execution',
            severity='INFO'
        )

        # Test performance logging
        log_performance_metric(
            operation='test_logging_command',
            duration=0.001
        )

        if test_all:
            self.stdout.write("Testing all configured loggers...")
            
            # Test all loggers defined in settings
            loggers_to_test = [
                'inventory.api',
                'inventory.security',
                'inventory.performance',
                'inventory.operations',
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
        test_logger = logging.getLogger('inventory.test')
        
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
        self.stdout.write(f'- {log_base_dir}/inventory_api.log (general logs)')
        self.stdout.write(f'- {log_base_dir}/inventory_api_debug.log (debug logs)')
        self.stdout.write(f'- {log_base_dir}/inventory_api_errors.log (error logs)')
        self.stdout.write(f'- {log_base_dir}/inventory_api_requests.log (API logs)')
        self.stdout.write(f'- {log_base_dir}/inventory_api_security.log (security logs)')
        self.stdout.write('- Console output should also show logs')
