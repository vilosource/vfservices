# Billing-API Django Project Logging Documentation

## Introduction

The Billing-API Django project implements a comprehensive logging solution designed for production API services. The logging system provides multiple log levels, specialized log files for different concerns, automatic request tracking, performance monitoring, and security event logging.

### Overall Configuration

The logging configuration is defined in `main/settings.py` and includes:

- **Log Base Directory**: Configurable via `LOG_BASE_DIR` environment variable (defaults to `/tmp`)

- **Multiple Log Files**:
  - `billing_api.log` - General application logs (10MB max, 5 backups)
  - `billing_api_debug.log` - Debug information (10MB max, 3 backups, only in DEBUG mode)
  - `billing_api_errors.log` - Error-only logs (5MB max, 10 backups)
  - `billing_api_requests.log` - API request logs (10MB max, 5 backups)
  - `billing_api_security.log` - Security event logs (5MB max, 10 backups)

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Formatters**: verbose, simple, detailed, api
- **Automatic Rotation**: Prevents log files from consuming excessive disk space

### Key Components

1. **Logging Utilities** (`billing/logging_utils.py`):
   - `@log_api_request` decorator for automatic API endpoint logging
   - Specialized logging functions for billing events, security events, and performance metrics
   - StructuredLogger class for consistent logging
   - Pre-configured loggers: billing_logger, api_logger, security_logger, performance_logger, events_logger

2. **Configured Loggers**:
   - Django system loggers (django, django.request, django.security, django.db.backends)
   - App-specific loggers (billing, billing.views, billing.models, billing.api)
   - Specialized loggers (billing.security, billing.performance)
   - Authentication logger (common.jwt_auth)
   - REST Framework logger

## How to Add Logging to Django Apps

### 1. Import the Required Loggers

In your Django app's views, models, or any Python file:

```python
from billing.logging_utils import (
    billing_logger,
    api_logger,
    security_logger,
    performance_logger,
    events_logger,
    log_billing_event,
    log_security_event,
    log_performance_metric
)
```

### 2. Use the API Request Decorator

For automatic API endpoint logging, use the `@log_api_request` decorator:

```python
from billing.logging_utils import log_api_request
from rest_framework.decorators import api_view

@api_view(['POST'])
@log_api_request
def process_payment(request):
    # Your API logic here
    return Response({'status': 'success'})
```

This automatically logs:
- Request start with user context and IP
- Request completion with status code
- Request duration (warns if >1 second)
- Any exceptions that occur

### 3. Log Billing Events

For billing-specific events, use the `log_billing_event` function:

```python
def create_subscription(user, plan):
    subscription = Subscription.objects.create(user=user, plan=plan)
    
    log_billing_event(
        request=request,
        event_type='subscription_created',
        user_id=user.id,
        details={
            'subscription_id': subscription.id,
            'plan_id': plan.id,
            'amount': plan.price,
            'currency': plan.currency
        }
    )
    
    return subscription
```

### 4. Log Security Events

For security-related events, use the `log_security_event` function:

```python
def admin_endpoint(request):
    if not request.user.is_staff:
        log_security_event(
            request=request,
            event_type='unauthorized_admin_access',
            severity='warning',
            details={
                'user_id': request.user.id,
                'attempted_endpoint': request.path
            }
        )
        return Response({'error': 'Unauthorized'}, status=403)
    
    # Admin logic here
```

### 5. Log Performance Metrics

For performance monitoring, use the `log_performance_metric` function:

```python
import time

def generate_report(request, report_type):
    start_time = time.time()
    
    # Generate report logic
    report = create_complex_report(report_type)
    
    duration = time.time() - start_time
    log_performance_metric(
        request=request,
        metric_name='report_generation',
        value=duration,
        unit='seconds',
        details={
            'report_type': report_type,
            'num_records': report.record_count
        }
    )
    
    return report
```

### 6. Use Structured Logging

For consistent structured logs across your app:

```python
from billing.logging_utils import StructuredLogger

# Create a logger for your module
logger = StructuredLogger('myapp.payments')

def process_refund(payment_id):
    logger.info('Processing refund', {
        'payment_id': payment_id,
        'amount': payment.amount,
        'reason': 'customer_request'
    })
    
    try:
        # Refund logic
        refund = payment.refund()
        logger.info('Refund successful', {
            'payment_id': payment_id,
            'refund_id': refund.id
        })
    except Exception as e:
        logger.error('Refund failed', {
            'payment_id': payment_id,
            'error': str(e)
        }, exc_info=True)
```

### 7. Module-Level Logging

For general logging within modules:

```python
import logging

# Get module logger
logger = logging.getLogger(__name__)

class PaymentProcessor:
    def process(self, payment):
        logger.debug(f"Processing payment {payment.id}")
        
        try:
            result = self._execute_payment(payment)
            logger.info(f"Payment {payment.id} processed successfully")
            return result
        except Exception as e:
            logger.error(f"Payment {payment.id} failed: {str(e)}", exc_info=True)
            raise
```

## Request Flow Tracking

The logging system enables tracking requests from start to end through several mechanisms:

### 1. Request Context

Every log entry from decorated endpoints includes:
- **User Information**: User ID, username (if authenticated)
- **Request Details**: HTTP method, path, query parameters
- **Client Information**: IP address (handles X-Forwarded-For), user agent
- **Timestamps**: ISO format timestamps for chronological ordering
- **Response Details**: Status code, duration

### 2. API Request Flow

The `@log_api_request` decorator tracks the complete request lifecycle:

```
1. Request arrives → Log entry: "API Request started"
2. View processing → Your custom logs within the view
3. Response generation → Log entry: "API Request completed" or "API Request failed"
4. Duration tracking → Warns if request takes >1 second
```

### 3. Following a Request

To follow a request through the logs:

1. **Filter by user**:
   ```bash
   grep "user_id.*123" /tmp/billing_api*.log | sort -k2
   ```

2. **Filter by IP address**:
   ```bash
   grep "ip.*192.168.1.100" /tmp/billing_api_requests.log
   ```

3. **Filter by endpoint**:
   ```bash
   grep "path.*/api/v1/payments" /tmp/billing_api_requests.log
   ```

4. **Combine multiple log files** for complete picture:
   ```bash
   tail -f /tmp/billing_api.log /tmp/billing_api_requests.log | grep "user_id.*123"
   ```

### 4. Example Request Flow

Here's how a typical API request appears in the logs:

```
# 1. Request arrives (billing_api_requests.log)
2024-01-20 10:30:00,123 INFO [billing.api] API Request started - User: john_doe (ID: 123), IP: 192.168.1.100, Method: POST, Path: /api/v1/payments/

# 2. View processing (billing_api.log)
2024-01-20 10:30:00,125 DEBUG [billing.views] Processing payment request for user 123
2024-01-20 10:30:00,150 INFO [billing.views] Payment validation successful

# 3. Billing event (billing_api.log)
2024-01-20 10:30:00,200 INFO [billing.events] Billing Event: payment_created - User: 123, Details: {'payment_id': 456, 'amount': 99.99, 'currency': 'USD'}

# 4. Performance metric (billing_api.log)
2024-01-20 10:30:00,220 INFO [billing.performance] Performance Metric: payment_processing - Value: 0.095 seconds

# 5. Request completed (billing_api_requests.log)
2024-01-20 10:30:00,225 INFO [billing.api] API Request completed - Status: 201, Duration: 0.102 seconds

# If slow (>1 second):
2024-01-20 10:30:02,000 WARNING [billing.api] Slow API request detected - Duration: 1.877 seconds
```

### 5. Debugging Tips

1. **Enable DEBUG logging** in development:
   ```python
   # In settings.py
   LOGGING['root']['level'] = 'DEBUG'
   ```

2. **Search logs efficiently**:
   ```bash
   # Find all errors for a specific user
   grep -E "ERROR.*user_id.*123" /tmp/billing_api*.log
   
   # Find slow requests
   grep "Slow API request" /tmp/billing_api_requests.log
   
   # Find security events
   cat /tmp/billing_api_security.log | grep "severity.*critical"
   ```

3. **Add request IDs for better tracking**:
   ```python
   import uuid
   
   @api_view(['POST'])
   @log_api_request
   def complex_operation(request):
       request_id = str(uuid.uuid4())
       logger = logging.getLogger(__name__)
       
       logger.info(f"Starting complex operation", extra={
           'request_id': request_id,
           'user_id': request.user.id
       })
       
       # Pass request_id through your service calls
       result = process_data(request_id, request.data)
       
       logger.info(f"Complex operation completed", extra={
           'request_id': request_id,
           'result_id': result.id
       })
   ```

## Testing the Logging System

The project includes a comprehensive testing command:

```bash
python manage.py test_logging [--level LEVEL]
```

This command:
- Tests all configured loggers
- Verifies log file creation
- Tests utility functions
- Supports different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

Example:
```bash
# Test all loggers at INFO level
python manage.py test_logging

# Test with DEBUG level
python manage.py test_logging --level DEBUG
```

## Best Practices

1. **Use the appropriate logger** for your context:
   - `billing_logger` for general billing operations
   - `api_logger` for API-specific events
   - `security_logger` for security events
   - `performance_logger` for performance metrics
   - `events_logger` for business events

2. **Include relevant context** in all log entries:
   - User ID for authenticated requests
   - Resource IDs (payment_id, subscription_id, etc.)
   - Operation results (success/failure)
   - Error details with stack traces

3. **Use appropriate log levels**:
   - DEBUG: Detailed information for debugging
   - INFO: General informational messages
   - WARNING: Warning conditions (slow requests, deprecations)
   - ERROR: Error conditions with stack traces
   - CRITICAL: Serious errors requiring immediate attention

4. **Structure your logs** for easy parsing:
   - Use consistent field names
   - Include all relevant IDs
   - Use the StructuredLogger for complex data

5. **Monitor performance**:
   - Use `log_performance_metric` for critical operations
   - Set up alerts for slow operations
   - Track trends over time

6. **Security considerations**:
   - Never log sensitive data (passwords, tokens, credit cards)
   - Use `log_security_event` for all security-related events
   - Review security logs regularly

## Log File Management

1. **Log Rotation**: Automatic via RotatingFileHandler
   - General logs: 10MB max, 5 backups
   - Debug logs: 10MB max, 3 backups
   - Error logs: 5MB max, 10 backups

2. **Log Location**: Configurable via `LOG_BASE_DIR` environment variable

3. **Monitoring**: Set up monitoring for:
   - Disk space usage
   - Error rate increases
   - Security events
   - Performance degradation

## Integration with Monitoring Systems

While not implemented by default, the logging system can be easily integrated with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- CloudWatch Logs
- Datadog
- Prometheus (via log parsing)

Consider adding:
- Centralized log aggregation
- Real-time alerting
- Log analytics and visualization
- Distributed tracing with correlation IDs