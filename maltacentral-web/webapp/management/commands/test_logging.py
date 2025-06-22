"""
Django management command to test logging configuration.
"""
import logging
from django.core.management.base import BaseCommand
from webapp.logging_utils import webapp_logger, security_logger, performance_logger, user_logger


class Command(BaseCommand):
    help = 'Test the logging configuration of the website'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing logging configuration...'))
        
        # Test different loggers
        loggers_to_test = [
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
        
        self.stdout.write(f'Testing {len(loggers_to_test)} loggers...')
        
        for logger_name, logger in loggers_to_test:
            self.stdout.write(f'Testing logger: {logger_name}')
            
            # Test different log levels
            logger.debug(f'DEBUG: Test message from {logger_name}')
            logger.info(f'INFO: Test message from {logger_name}')
            logger.warning(f'WARNING: Test message from {logger_name}')
            logger.error(f'ERROR: Test message from {logger_name}')
            
            # Test structured logging
            logger.info(
                f'Structured log from {logger_name}',
                extra={
                    'logger_name': logger_name,
                    'test_data': 'management_command_test',
                    'test_number': 456,
                    'test_bool': True,
                }
            )
        
        self.stdout.write('Testing custom webapp loggers...')
        
        # Test custom webapp loggers
        webapp_logger.info('Test message from webapp_logger', test_key='management_test')
        security_logger.warning('Test security event from management command', event_type='test')
        performance_logger.debug('Test performance log from management command', duration_ms=50)
        user_logger.info('Test user action from management command', user='management_command', action='test_logging')
        
        self.stdout.write('Testing exception logging...')
        
        # Test exception logging
        try:
            raise ValueError('This is a test exception from management command')
        except Exception:
            logging.getLogger('webapp').error('Test exception logging from management command', exc_info=True)
        
        self.stdout.write(self.style.SUCCESS('Logging test completed!'))
        self.stdout.write('Check the following log files:')
        self.stdout.write('- /tmp/website.log (main log)')
        self.stdout.write('- /tmp/website_debug.log (debug log)')
        self.stdout.write('- /tmp/website_errors.log (error log)')
        self.stdout.write('- /tmp/website_performance.log (performance log)')
        self.stdout.write('- /tmp/website_security.log (security log)')
