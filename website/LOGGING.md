# Django Website Logging Documentation

This document describes the comprehensive logging system implemented for the Django website project.

## Overview

The website now includes a robust logging configuration that captures:
- All HTTP requests and responses
- View execution flow with timing
- Database operations
- Security events
- User actions
- Error tracking
- Performance monitoring

## Logging Configuration

The logging is configured in `main/settings.py` with the following features:

### Log Files
- `/tmp/website.log` - Main application log (INFO level and above)
- `/tmp/website_debug.log` - Debug information (DEBUG level, only in DEBUG mode)
- `/tmp/website_errors.log` - Error logs (ERROR level and above)
- `/tmp/website_performance.log` - Performance metrics
- `/tmp/website_security.log` - Security events

### Log Formatters
- **verbose**: Detailed format with timestamp, level, module, function, line number
- **detailed**: Human-readable format for console output
- **json**: JSON format for structured logging
- **simple**: Basic format for simple logging needs

### Loggers
- `main.*` - Main project loggers
- `webapp.*` - Web application loggers
- `accounts.*` - Authentication and accounts loggers
- `webapp.security` - Security event logger
- `webapp.performance` - Performance monitoring logger
- `webapp.user_actions` - User action tracking logger
- `webapp.middleware` - Request/response middleware logger

## View Logging

All views now include comprehensive logging:

### Automatic Logging
Views are decorated with `@log_view_access` which automatically logs:
- View access with user information
- Request details (IP, user agent, etc.)
- Performance timing
- Errors with full stack traces

### Manual Logging
Views also include manual logging for specific events:
- Template rendering
- Business logic execution
- Error conditions
- Security-relevant events

## Usage Examples

### Testing the Logging System
```bash
# Test logging configuration
python manage.py test_logging

# Or run the standalone test script
python test_logging.py
```

### In Views
```python
import logging
from webapp.logging_utils import log_view_access, webapp_logger, get_client_ip

logger = logging.getLogger(__name__)

@log_view_access('my_view')
def my_view(request):
    logger.info(f"Processing request for user: {request.user}")
    
    try:
        # View logic here
        logger.debug("Business logic executed successfully")
        return render(request, 'template.html')
    except Exception as e:
        logger.error(f"Error in view: {str(e)}", exc_info=True)
        raise
```

### Security Logging
```python
from webapp.logging_utils import security_logger

# Log authentication events
security_logger.log_auth_attempt(request, username, success=True)

# Log permission denials
security_logger.log_permission_denied(request, resource="admin_panel")

# Log suspicious activity
security_logger.log_suspicious_activity(request, "Multiple failed login attempts")
```

### Performance Logging
```python
from webapp.logging_utils import performance_logger

# Log slow operations
performance_logger.debug("Database query executed", duration_ms=250, query_type="SELECT")
```

## Middleware Logging

The `RequestLoggingMiddleware` automatically logs:
- All incoming requests with full context
- Response status codes and timing
- Slow request warnings (>1s)
- Unhandled exceptions
- Request/response sizes

## Security Features

The logging system includes security-focused features:
- Automatic filtering of sensitive data (passwords, tokens, etc.)
- IP address tracking
- User agent logging
- Session tracking
- Authentication event logging
- Suspicious activity detection

## Monitoring and Alerting

Log files can be monitored using tools like:
- `tail -f /tmp/website.log` - Real-time log monitoring
- Log aggregation tools (ELK stack, Splunk, etc.)
- Custom alerting based on ERROR/CRITICAL log levels

## Best Practices

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General operational information
   - WARNING: Unexpected behavior that doesn't prevent operation
   - ERROR: Serious problems that prevent operation
   - CRITICAL: Very serious errors that may cause program termination

2. **Include relevant context**:
   - User information
   - Request details
   - Timing information
   - Error details with stack traces

3. **Be mindful of sensitive data**:
   - Never log passwords, tokens, or personal information
   - Use the built-in filtering for sensitive fields
   - Sanitize user input before logging

4. **Monitor performance**:
   - Log slow operations
   - Track database query counts
   - Monitor response times

## Log Rotation

The logging configuration uses `RotatingFileHandler` to prevent log files from growing too large:
- Main logs: 10MB per file, 5 backup files
- Error logs: 5MB per file, 10 backup files
- Debug logs: 10MB per file, 3 backup files

## Integration with External Services

The structured logging format makes it easy to integrate with:
- Elasticsearch + Kibana
- Splunk
- Datadog
- New Relic
- Custom monitoring solutions

## Troubleshooting

If logging isn't working:
1. Check that log directories exist and are writable (`/tmp/`)
2. Verify Django settings are loaded correctly
3. Test with the management command: `python manage.py test_logging`
4. Check for import errors in logging utilities

## Future Enhancements

Planned improvements:
- JSON-structured logging for better parsing
- Integration with external monitoring services
- Custom log aggregation dashboard
- Automated alerting based on log patterns
- Log analysis and reporting tools
