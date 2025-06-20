"""
Management command to test logging configuration.
"""
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from azure_costs.logging_utils import (
    log_azure_cost_event,
    log_security_event,
    log_performance_metric,
    azure_costs_logger,
    api_logger,
    security_logger,
    performance_logger
)


class Command(BaseCommand):
    help = 'Test logging configuration for Azure Costs API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--level',
            type=str,
            default='INFO',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Log level to test'
        )

    def handle(self, *args, **options):
        log_level = options['level'].upper()
        
        self.stdout.write(f"Testing Azure Costs API logging at {log_level} level...")
        self.stdout.write("=" * 60)
        
        # Test module loggers
        self.stdout.write("\n1. Testing module loggers:")
        self.stdout.write("-" * 40)
        
        loggers_to_test = [
            ('django', logging.getLogger('django')),
            ('django.request', logging.getLogger('django.request')),
            ('django.security', logging.getLogger('django.security')),
            ('main', logging.getLogger('main')),
            ('azure_costs', logging.getLogger('azure_costs')),
            ('azure_costs.views', logging.getLogger('azure_costs.views')),
            ('azure_costs.models', logging.getLogger('azure_costs.models')),
            ('azure_costs.api', logging.getLogger('azure_costs.api')),
            ('azure_costs.security', logging.getLogger('azure_costs.security')),
            ('azure_costs.performance', logging.getLogger('azure_costs.performance')),
            ('common.jwt_auth', logging.getLogger('common.jwt_auth')),
            ('rest_framework', logging.getLogger('rest_framework')),
        ]
        
        for logger_name, logger in loggers_to_test:
            self.stdout.write(f"Testing logger: {logger_name}")
            
            if log_level == 'DEBUG':
                logger.debug(f"Test DEBUG message from {logger_name}")
            if log_level in ['DEBUG', 'INFO']:
                logger.info(f"Test INFO message from {logger_name}")
            if log_level in ['DEBUG', 'INFO', 'WARNING']:
                logger.warning(f"Test WARNING message from {logger_name}")
            if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
                logger.error(f"Test ERROR message from {logger_name}")
            if log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                logger.critical(f"Test CRITICAL message from {logger_name}")
        
        # Test structured loggers
        self.stdout.write("\n2. Testing structured loggers:")
        self.stdout.write("-" * 40)
        
        # Test azure_costs_logger
        azure_costs_logger.info("Test azure costs logger", {
            'test': True,
            'timestamp': timezone.now().isoformat(),
            'details': {'message': 'This is a test'}
        })
        
        # Test api_logger
        api_logger.info("Test API logger", {
            'endpoint': 'test_endpoint',
            'method': 'GET',
            'status_code': 200,
            'duration': 0.123
        })
        
        # Test security_logger
        security_logger.warning("Test security logger", {
            'event_type': 'test_security_event',
            'ip': '127.0.0.1',
            'user': 'test_user'
        })
        
        # Test performance_logger
        performance_logger.info("Test performance logger", {
            'metric_name': 'test_operation',
            'value': 0.456,
            'unit': 'seconds'
        })
        
        # Test utility functions (with mock request)
        self.stdout.write("\n3. Testing utility functions:")
        self.stdout.write("-" * 40)
        
        # Create a mock request
        class MockRequest:
            def __init__(self):
                self.user = type('User', (), {
                    'id': 123,
                    'username': 'test_user',
                    'is_authenticated': True
                })()
                self.path = '/api/test'
                self.method = 'GET'
                self.META = {
                    'HTTP_USER_AGENT': 'Test Agent',
                    'REMOTE_ADDR': '127.0.0.1'
                }
        
        mock_request = MockRequest()
        
        # Test log_azure_cost_event
        log_azure_cost_event(
            request=mock_request,
            event_type='cost_analysis_requested',
            resource_id='test-resource-123',
            cost_amount=123.45,
            details={'subscription': 'test-sub'}
        )
        
        # Test log_security_event
        log_security_event(
            request=mock_request,
            event_type='unauthorized_access_attempt',
            severity='warning',
            details={'attempted_resource': 'admin_panel'}
        )
        
        # Test log_performance_metric
        log_performance_metric(
            request=mock_request,
            metric_name='azure_api_call',
            value=1.234,
            unit='seconds',
            details={'api_endpoint': 'cost_management'}
        )
        
        # Test exception logging
        self.stdout.write("\n4. Testing exception logging:")
        self.stdout.write("-" * 40)
        
        try:
            raise ValueError("Test exception for logging")
        except ValueError:
            logger = logging.getLogger('azure_costs')
            logger.error("Test exception caught", exc_info=True)
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("Logging test completed successfully!"))
        self.stdout.write("Check the following log files:")
        self.stdout.write("- /tmp/azure_costs.log")
        self.stdout.write("- /tmp/azure_costs_debug.log (if DEBUG=True)")
        self.stdout.write("- /tmp/azure_costs_errors.log")
        self.stdout.write("- /tmp/azure_costs_requests.log")
        self.stdout.write("- /tmp/azure_costs_security.log")