# Billing API - Logging Setup

This document describes the comprehensive logging configuration for the Billing API service.

## Overview

The Billing API has a structured logging system that captures various types of events:
- API requests and responses
- Billing operations and transactions
- Security events
- Performance metrics
- Error conditions

## Log Configuration

### Log Files

The log directory is configurable through the `LOG_BASE_DIR` environment variable (defaults to `/tmp/`):

```bash
# Default setup
python manage.py runserver  # logs to /tmp/

# Production setup
export LOG_BASE_DIR=/var/log/billing
python manage.py runserver  # logs to /var/log/billing/

# Testing with custom directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging
```

The following log files are created in the configured directory:

- **billing.log** - General application logs
- **billing_debug.log** - Debug level logs (development only)
- **billing_error.log** - Error and critical logs
- **billing_api.log** - API request/response logs
- **billing_security.log** - Security-related events

### Log Levels

The logging configuration supports all standard Python logging levels:
- `DEBUG` - Detailed diagnostic information
- `INFO` - General information about application flow
- `WARNING` - Something unexpected happened but the application is still working
- `ERROR` - An error occurred but the application can continue
- `CRITICAL` - A serious error occurred that may prevent the application from continuing

### Loggers

The following loggers are configured:

- `billing` - Main application logger
- `billing.api` - API-specific logs
- `billing.security` - Security events
- `billing.performance` - Performance metrics
- `billing.business` - Business logic events
- `django.request` - Django request handling
- `django.security` - Django security events

## Logging Utilities

### Available Functions

#### `log_api_request(endpoint_name)`
Decorator for logging API endpoint access and performance.

```python
@log_api_request('health_check')
@api_view(['GET'])
def health(request):
    return Response({'status': 'ok'})
```

#### `log_billing_event(event_type, user, amount, currency, extra_data)`
Log billing-specific events.

```python
log_billing_event(
    event_type='payment_processed',
    user=request.user,
    amount=100.00,
    currency='USD',
    extra_data={'payment_method': 'credit_card'}
)
```

#### `log_security_event(event_type, request, user, severity, extra_data)`
Log security-related events.

```python
log_security_event(
    event_type='failed_login_attempt',
    request=request,
    severity='WARNING',
    extra_data={'attempts': 3}
)
```

#### `log_performance_metric(operation, duration, extra_data)`
Log performance metrics.

```python
log_performance_metric(
    operation='database_query',
    duration=0.145,
    extra_data={'query_type': 'complex_join'}
)
```

### StructuredLogger Class

The `StructuredLogger` class provides a consistent interface for structured logging:

```python
from billing.logging_utils import StructuredLogger

logger = StructuredLogger('billing.custom')
logger.info('Operation completed', user_id=123, operation='update_billing')
logger.error('Operation failed', error_code='BIL001', details='Invalid amount')
```

## Testing Logging

### Management Command

Test the logging configuration using the management command:

```bash
# Test basic logging (default directory)
python manage.py test_logging

# Test with custom log directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging

# Test all loggers with custom directory
LOG_BASE_DIR=/var/log/billing python manage.py test_logging --all-loggers

# Test specific log level
python manage.py test_logging --level debug
```

### Manual Testing

```python
import logging
from billing.logging_utils import log_billing_event

# Test standard logging
logger = logging.getLogger('billing')
logger.info('Test message')

# Test utility functions
log_billing_event('test_event', extra_data={'test': True})
```

## Best Practices

### 1. Use Appropriate Log Levels
- Use `DEBUG` for detailed diagnostic information
- Use `INFO` for general application flow
- Use `WARNING` for unexpected but recoverable conditions
- Use `ERROR` for error conditions
- Use `CRITICAL` for serious errors

### 2. Include Context
Always include relevant context in log messages:
- User information
- Request details
- Transaction IDs
- Timestamps

### 3. Structured Logging
Use the structured logging utilities for consistent log formatting:

```python
# Good
logger.info('Payment processed', extra={
    'user_id': user.id,
    'amount': amount,
    'currency': currency,
    'transaction_id': transaction_id
})

# Avoid
logger.info(f'Payment of {amount} {currency} processed for user {user.id}')
```

### 4. Security Considerations
- Never log sensitive information (passwords, API keys, full credit card numbers)
- Use structured logging for security events
- Monitor security logs regularly

### 5. Performance Logging
- Log slow operations (> 1 second)
- Include operation type and duration
- Use performance metrics for optimization

## Configuration Details

The logging configuration is defined in `billing/main/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
            'style': '{',
        },
    },
    # ... handlers and loggers configuration
}
```

## Monitoring and Alerting

### Log Monitoring
- Monitor error logs for application issues
- Set up alerts for critical errors
- Review security logs regularly

### Performance Monitoring
- Track slow operations
- Monitor API response times
- Set up alerts for performance degradation

### Business Metrics
- Monitor billing events
- Track transaction volumes
- Alert on unusual patterns

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check file permissions and log file paths
2. **Too many debug logs**: Adjust log levels in settings
3. **Log rotation**: Implement log rotation for production environments

### Debug Mode

For development, enable debug logging:

```python
LOGGING['loggers']['billing']['level'] = 'DEBUG'
```

### Production Considerations

For production deployments:
- Use appropriate log levels (INFO or WARNING)
- Implement log rotation
- Send logs to centralized logging system
- Monitor disk space usage
- Set up log aggregation and analysis tools
