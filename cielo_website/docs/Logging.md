# CIELO Website Django Project Logging Documentation

## Introduction

The CIELO website Django project implements a comprehensive logging solution designed for production environments with a focus on security, performance monitoring, and RBAC/ABAC integration. The logging system provides multiple log levels, specialized log files, automatic sensitive data filtering, request tracking, and extensive middleware integration.

### Overall Configuration

The logging configuration is defined in `main/settings.py` and includes:

- **Log Base Directory**: Configurable via `LOG_BASE_DIR` environment variable (defaults to `/tmp`)

- **Multiple Log Files**:
  - `cielo_website.log` - General application logs (10MB max, 5 backups)
  - `cielo_website_debug.log` - Debug information (10MB max, 3 backups, only in DEBUG mode)
  - `cielo_website_errors.log` - Error logs (5MB max, 10 backups)
  - `cielo_website_performance.log` - Performance metrics in JSON format (10MB max, 5 backups)
  - `cielo_website_security.log` - Security events (5MB max, 10 backups)

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Formatters**: verbose, simple, json, detailed
- **Automatic Rotation**: Prevents log files from consuming excessive disk space

### Key Components

1. **RequestLoggingMiddleware** (`webapp/middleware.py`):
   - Comprehensive request/response logging
   - Automatic sensitive data filtering
   - Request duration tracking with slow request detection
   - Exception capture and logging

2. **CieloAccessMiddleware** (`webapp/middleware.py`):
   - RBAC/ABAC permission logging
   - Access denial tracking
   - Role-based access control logging

3. **Logging Utilities** (`webapp/logging_utils.py`):
   - Helper functions for standardized logging
   - `@log_view_access` decorator for automatic view logging
   - StructuredLogger class for consistent logging
   - Pre-configured loggers for different concerns

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

@log_view_access('my_view_name')
def my_view(request):
    # Your view logic here
    return render(request, 'template.html')
```

This automatically logs:
- View entry with user context and request details
- View exit with response status
- Execution time
- Any exceptions that occur with full stack traces

### 3. Log User Actions

For tracking user activities:

```python
@login_required
def update_profile(request):
    if request.method == 'POST':
        # Update profile logic
        profile = request.user.profile
        profile.bio = request.POST.get('bio')
        profile.save()
        
        # Log the action
        log_user_action(
            request,
            action='profile_updated',
            details={
                'user_id': request.user.id,
                'fields_updated': ['bio']
            }
        )
        
        return redirect('profile')
```

### 4. Log Security Events

For security-related events:

```python
def admin_panel(request):
    if not request.user.has_perm('webapp.access_admin'):
        log_security_event(
            request,
            event_type='unauthorized_admin_access',
            severity='warning',
            details={
                'user_id': request.user.id,
                'attempted_url': request.path
            }
        )
        return HttpResponseForbidden()
    
    # Admin panel logic
```

### 5. Log Performance Metrics

For performance monitoring:

```python
import time

def generate_report(request):
    start_time = time.time()
    
    # Complex report generation
    report_data = compile_complex_report()
    
    # Log performance
    log_performance(
        request,
        metric_name='report_generation',
        value=time.time() - start_time,
        unit='seconds',
        details={
            'report_type': 'monthly_summary',
            'data_points': len(report_data)
        }
    )
    
    return JsonResponse(report_data)
```

### 6. Use Structured Logging

For consistent structured logs across your app:

```python
from webapp.logging_utils import StructuredLogger

# Create a logger for your module
logger = StructuredLogger('myapp.services')

def process_data(data):
    logger.info('Processing data batch', {
        'batch_size': len(data),
        'source': 'api_import'
    })
    
    try:
        result = transform_data(data)
        logger.info('Data processing completed', {
            'records_processed': len(result),
            'success': True
        })
        return result
    except Exception as e:
        logger.error('Data processing failed', {
            'error': str(e),
            'batch_size': len(data)
        }, exc_info=True)
        raise
```

### 7. RBAC/ABAC Integration Logging

When working with CIELO roles and permissions:

```python
from webapp.middleware import requires_cielo_role

@requires_cielo_role(['admin', 'supervisor'])
def sensitive_operation(request):
    # The middleware automatically logs permission checks
    # Add additional logging for the operation
    logger.info('Sensitive operation accessed', extra={
        'user_id': request.user.id,
        'user_roles': getattr(request.user, 'cielo_roles', []),
        'operation': 'data_export'
    })
    
    # Operation logic
```

## Request Flow Tracking

The logging system enables comprehensive request tracking through multiple mechanisms:

### 1. Request Context

Every log entry includes rich request context:
- **User Information**: User ID, username, email, authentication status
- **Request Details**: HTTP method, path, query parameters, content type
- **Client Information**: IP address (with X-Forwarded-For support), user agent
- **Session Information**: Session key for tracking user sessions
- **Timestamps**: ISO format timestamps for chronological ordering
- **Performance Metrics**: Request duration automatically calculated

### 2. Middleware Flow

The request flows through multiple middleware layers, each adding logging:

```
1. RequestLoggingMiddleware → Logs request start
2. CieloAccessMiddleware → Logs RBAC/ABAC checks
3. View Processing → View decorator logs
4. Response Generation → Middleware logs response
5. Total Duration → Performance metrics logged
```

### 3. Following a Request

To follow a request through the logs:

1. **Filter by user**:
   ```bash
   grep "user_id.*123" /tmp/cielo_website*.log | sort -k2
   ```

2. **Filter by session**:
   ```bash
   grep "session_key.*abc123" /tmp/cielo_website.log
   ```

3. **Filter by IP address**:
   ```bash
   grep "ip.*192.168.1.100" /tmp/cielo_website.log
   ```

4. **Track slow requests**:
   ```bash
   grep "Slow request detected" /tmp/cielo_website.log
   ```

5. **Monitor security events**:
   ```bash
   tail -f /tmp/cielo_website_security.log
   ```

### 4. Example Request Flow

Here's how a typical request appears in the logs:

```
# 1. Request arrives (cielo_website.log)
2024-01-20 10:30:00,123 INFO [webapp.middleware] Request started - Method: GET, Path: /dashboard/, User: john_doe (123), IP: 192.168.1.100

# 2. RBAC check (cielo_website_security.log)
2024-01-20 10:30:00,125 INFO [webapp.middleware] CIELO access check - User: 123, Required roles: ['user'], Has roles: ['user', 'admin'], Access: granted

# 3. View processing (cielo_website.log)
2024-01-20 10:30:00,130 INFO [webapp.views] View accessed: dashboard - User: john_doe (123)
2024-01-20 10:30:00,132 DEBUG [webapp.views] Starting dashboard rendering for user 123

# 4. External service call (cielo_website.log)
2024-01-20 10:30:00,150 INFO [webapp.views] Fetching aggregated menu from identity provider
2024-01-20 10:30:00,250 INFO [webapp.views] Successfully fetched menu with 5 items

# 5. User action (cielo_website.log)
2024-01-20 10:30:00,280 INFO [webapp.user_actions] User action: dashboard_viewed - User: 123, Details: {'menu_items': 5}

# 6. View completion (cielo_website.log)
2024-01-20 10:30:00,300 INFO [webapp.views] View completed: dashboard - Duration: 0.170 seconds

# 7. Response (cielo_website.log)
2024-01-20 10:30:00,305 INFO [webapp.middleware] Request completed - Status: 200, Duration: 0.182 seconds

# 8. Performance metric (cielo_website_performance.log)
{"timestamp": "2024-01-20T10:30:00.306Z", "metric": "request_duration", "value": 0.182, "unit": "seconds", "path": "/dashboard/", "user_id": 123}
```

### 5. Debugging Tips

1. **Enable DEBUG logging** in development:
   ```python
   # In settings.py
   LOGGING['root']['level'] = 'DEBUG'
   ```

2. **Use structured search** for JSON performance logs:
   ```bash
   # Find slow requests
   jq 'select(.value > 1)' /tmp/cielo_website_performance.log
   
   # Aggregate by path
   jq -s 'group_by(.path) | map({path: .[0].path, avg: (map(.value) | add/length)})' /tmp/cielo_website_performance.log
   ```

3. **Track user sessions**:
   ```bash
   # Follow a user's complete session
   SESSION="abc123..."
   grep "session_key.*$SESSION" /tmp/cielo_website*.log | sort -k2
   ```

4. **Monitor authentication issues**:
   ```bash
   # Find failed logins
   grep "login_failed" /tmp/cielo_website_security.log
   
   # Find permission denials
   grep "permission_denied\|access_denied" /tmp/cielo_website_security.log
   ```

5. **Create correlation IDs** for complex flows:
   ```python
   import uuid
   
   def complex_workflow(request):
       correlation_id = str(uuid.uuid4())
       
       webapp_logger.info('Starting complex workflow', extra={
           'correlation_id': correlation_id,
           'user_id': request.user.id
       })
       
       # Pass correlation_id through all function calls
       step1_result = process_step1(correlation_id, request.data)
       step2_result = process_step2(correlation_id, step1_result)
       
       webapp_logger.info('Complex workflow completed', extra={
           'correlation_id': correlation_id,
           'duration': calculate_duration()
       })
   ```

## Testing the Logging System

Test your logging configuration:

```python
# In Django shell
from webapp.logging_utils import webapp_logger, security_logger, performance_logger

# Test different log levels
webapp_logger.debug("Debug message")
webapp_logger.info("Info message")
webapp_logger.warning("Warning message")
webapp_logger.error("Error message")

# Test structured logging
webapp_logger.info("Test event", extra={
    'user_id': 123,
    'action': 'test',
    'details': {'key': 'value'}
})

# Verify log files exist
import os
log_dir = '/tmp'  # or your configured LOG_BASE_DIR
for log_file in ['cielo_website.log', 'cielo_website_errors.log', 'cielo_website_security.log']:
    print(f"{log_file}: {'exists' if os.path.exists(os.path.join(log_dir, log_file)) else 'missing'}")
```

## Best Practices

1. **Always use the decorator** on views for consistent logging
2. **Include user context** in all log entries when available
3. **Use appropriate log levels**:
   - DEBUG: Detailed debugging information
   - INFO: General informational messages
   - WARNING: Warning conditions (slow requests, deprecated features)
   - ERROR: Error conditions that should be investigated
   - CRITICAL: Serious errors requiring immediate attention

4. **Structure your logs** for easy parsing and analysis
5. **Never log sensitive data** directly (middleware filters automatically)
6. **Use specialized loggers** for different concerns:
   - `security_logger` for authentication and authorization events
   - `performance_logger` for performance metrics
   - `user_logger` for user actions

7. **Monitor performance**:
   - Set up alerts for slow requests (>1 second)
   - Track error rates
   - Monitor authentication failures

8. **RBAC/ABAC logging**:
   - Log all permission checks
   - Track role changes
   - Monitor access patterns

## Security Considerations

The logging system includes several security features:

1. **Automatic Sensitive Data Filtering**:
   - Passwords
   - API tokens
   - Credit card numbers
   - Social Security Numbers
   - CSRF tokens

2. **Security Event Tracking**:
   - Failed authentication attempts
   - Permission denials
   - Suspicious activities
   - RBAC/ABAC violations

3. **Audit Trail**:
   - User actions are logged with full context
   - IP addresses tracked for all requests
   - Session tracking for user activity correlation

Always review logs before sharing to ensure no sensitive data is exposed. The middleware automatically filters known sensitive patterns, but always verify.