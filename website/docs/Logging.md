# Website Django Project Logging Documentation

## Introduction

The website Django project implements a comprehensive logging solution designed for production environments. The logging system provides multiple log levels, specialized log files, automatic sensitive data filtering, performance monitoring, and security event tracking.

### Overall Configuration

The logging configuration is defined in `main/settings.py` and includes:

- **Multiple Log Handlers**:
  - Console handler for development
  - File-based handlers with rotation for production
  - Specialized handlers for different log types

- **Log Files** (all stored in `/tmp/`):
  - `website.log` - Main application log
  - `website_debug.log` - Debug information (only in DEBUG mode)
  - `website_errors.log` - Error logs
  - `website_performance.log` - Performance metrics
  - `website_security.log` - Security events

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Formatters**: verbose, detailed, json, simple
- **Automatic Rotation**: Prevents log files from growing too large

### Key Components

1. **RequestLoggingMiddleware** (`webapp/middleware.py`):
   - Logs all incoming requests and responses
   - Tracks request duration and performance
   - Filters sensitive data automatically
   - Captures unhandled exceptions

2. **Enhanced Logging Utilities** (`webapp/enhanced_logging.py`):
   - RequestLogger, ViewLogger, DatabaseLogger, SecurityLogger
   - Decorators for automatic logging

3. **Logging Utilities** (`webapp/logging_utils.py`):
   - Helper functions for standardized logging
   - Pre-configured loggers
   - StructuredLogger class

## How to Add Logging to Django Apps

### 1. Import the Required Loggers

In your Django app's views, models, or any Python file:

```python
from webapp.logging_utils import (
    webapp_logger,
    security_logger,
    performance_logger,
    user_logger,
    log_user_action,
    log_performance,
    log_security_event
)
```

### 2. Use the View Access Decorator

For automatic view logging, use the `@log_view_access` decorator:

```python
from webapp.logging_utils import log_view_access

@log_view_access
def my_view(request):
    # Your view logic here
    return render(request, 'template.html')
```

This automatically logs:
- View entry with user context
- View exit with response status
- Execution time
- Any exceptions that occur

### 3. Log Custom Events

#### User Actions
```python
def process_order(request, order_id):
    # Process the order
    order = Order.objects.get(id=order_id)
    order.status = 'processed'
    order.save()
    
    # Log the action
    log_user_action(
        request,
        action='order_processed',
        details={'order_id': order_id, 'new_status': 'processed'}
    )
```

#### Performance Metrics
```python
def complex_calculation(request):
    import time
    start_time = time.time()
    
    # Perform complex calculation
    result = perform_calculation()
    
    # Log performance
    log_performance(
        request,
        metric_name='complex_calculation',
        value=time.time() - start_time,
        unit='seconds'
    )
    
    return JsonResponse({'result': result})
```

#### Security Events
```python
def admin_action(request):
    if not request.user.has_perm('app.admin_permission'):
        log_security_event(
            request,
            event_type='permission_denied',
            severity='warning',
            details={'required_permission': 'app.admin_permission'}
        )
        return HttpResponseForbidden()
    
    # Proceed with admin action
```

### 4. Use Structured Logging

For consistent structured logs across your app:

```python
from webapp.logging_utils import StructuredLogger

logger = StructuredLogger('myapp')

def my_function(request):
    logger.info('Processing user request', {
        'user_id': request.user.id,
        'action': 'data_export',
        'format': 'csv'
    })
```

### 5. Enhanced Logging Decorators

For more detailed logging, use the enhanced logging decorators:

```python
from webapp.enhanced_logging import enhanced_log_view, log_database_queries

@enhanced_log_view
@log_database_queries
def data_intensive_view(request):
    # This will automatically log:
    # - View execution time
    # - All database queries
    # - Slow queries (>100ms)
    # - Request/response details
    
    users = User.objects.filter(is_active=True)
    return render(request, 'users.html', {'users': users})
```

## Request Flow Tracking

The logging system enables tracking requests from start to end through several mechanisms:

### 1. Request Context

Every log entry includes request context when available:
- **User Information**: User ID, username, email
- **Request Details**: Method, path, query parameters
- **Client Information**: IP address, user agent
- **Session Information**: Session key for tracking across requests
- **Timestamps**: ISO format timestamps for chronological ordering

### 2. Middleware Flow

The `RequestLoggingMiddleware` logs the complete request lifecycle:

```
1. Request arrives → Log entry with request details
2. View processing → Log entries from view decorator
3. Database queries → Query logs with execution time
4. Response generation → Log response status and size
5. Total duration → Performance log with request timing
```

### 3. Following a Request

To follow a request through the logs:

1. **Identify the request** by timestamp and user:
   ```bash
   grep "user_id\": 123" /tmp/website.log | grep "2024-01-20T10:30"
   ```

2. **Use session key** to track all requests in a session:
   ```bash
   grep "session_key\": \"abc123\"" /tmp/website.log
   ```

3. **Filter by request path**:
   ```bash
   grep "path\": \"/api/orders\"" /tmp/website.log
   ```

4. **Combine multiple log files** for complete picture:
   ```bash
   tail -f /tmp/website.log /tmp/website_performance.log | grep "user_id\": 123"
   ```

### 4. Example Request Flow

Here's how a typical request appears in the logs:

```json
// 1. Request arrives (website.log)
{
  "timestamp": "2024-01-20T10:30:00.123Z",
  "level": "INFO",
  "logger": "webapp.middleware",
  "message": "Request started",
  "user_id": 123,
  "username": "john_doe",
  "method": "POST",
  "path": "/api/orders/create",
  "ip": "192.168.1.100",
  "session_key": "abc123..."
}

// 2. View processing (website.log)
{
  "timestamp": "2024-01-20T10:30:00.125Z",
  "level": "INFO",
  "logger": "webapp.views",
  "message": "View entered: create_order",
  "user_id": 123,
  "session_key": "abc123..."
}

// 3. Database queries (website_debug.log)
{
  "timestamp": "2024-01-20T10:30:00.250Z",
  "level": "DEBUG",
  "logger": "webapp.db",
  "message": "Database query",
  "query": "INSERT INTO orders...",
  "duration": 0.015,
  "user_id": 123
}

// 4. User action (website.log)
{
  "timestamp": "2024-01-20T10:30:00.300Z",
  "level": "INFO",
  "logger": "user_actions",
  "message": "User action: order_created",
  "user_id": 123,
  "details": {"order_id": 456, "total": 99.99}
}

// 5. Response (website.log)
{
  "timestamp": "2024-01-20T10:30:00.350Z",
  "level": "INFO",
  "logger": "webapp.middleware",
  "message": "Request completed",
  "user_id": 123,
  "status_code": 201,
  "duration": 0.227,
  "path": "/api/orders/create"
}

// 6. Performance metric (website_performance.log)
{
  "timestamp": "2024-01-20T10:30:00.351Z",
  "level": "INFO",
  "logger": "performance",
  "message": "Request performance",
  "path": "/api/orders/create",
  "duration": 0.227,
  "user_id": 123
}
```

### 5. Debugging Tips

1. **Enable DEBUG logging** in development:
   ```python
   # In settings.py
   LOGGING['root']['level'] = 'DEBUG'
   ```

2. **Use structured search** with jq for JSON logs:
   ```bash
   cat /tmp/website.log | jq 'select(.user_id == 123 and .timestamp > "2024-01-20T10:00:00")'
   ```

3. **Create custom loggers** for specific debugging:
   ```python
   import logging
   debug_logger = logging.getLogger('myapp.debug')
   debug_logger.debug('Detailed debug info', extra={'context': 'specific_feature'})
   ```

4. **Use correlation IDs** (manual implementation):
   ```python
   import uuid
   
   def my_view(request):
       correlation_id = str(uuid.uuid4())
       webapp_logger.info('Starting process', extra={'correlation_id': correlation_id})
       
       # Pass correlation_id through your function calls
       result = process_data(correlation_id)
       
       webapp_logger.info('Process complete', extra={'correlation_id': correlation_id})
   ```

## Testing the Logging System

The project includes testing utilities:

1. **Management Command**:
   ```bash
   python manage.py test_logging
   ```

2. **Standalone Test Script**:
   ```bash
   python test_logging.py
   ```

These tools verify that all loggers are properly configured and working.

## Best Practices

1. **Always use structured logging** with the provided utilities
2. **Include user context** in all log entries when available
3. **Use appropriate log levels** (DEBUG for development, INFO for general, ERROR for exceptions)
4. **Never log sensitive data** directly (the middleware filters it automatically)
5. **Use the specialized loggers** (security_logger for security events, performance_logger for metrics)
6. **Add meaningful details** to log entries to aid debugging
7. **Use decorators** for consistent logging across views
8. **Monitor log file sizes** (rotation is automatic but check disk space)

## Security Considerations

The logging system automatically filters sensitive data patterns:
- Passwords
- API tokens
- Credit card numbers
- Social Security Numbers
- Email addresses (in certain contexts)

Always review logs before sharing to ensure no sensitive data is exposed.