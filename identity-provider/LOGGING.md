# Identity Provider - Logging Setup

This document describes the comprehensive logging configuration for the Identity Provider service.

## Overview

The Identity Provider has a specialized logging system that captures authentication, authorization, and security events:
- Authentication attempts and outcomes
- JWT token operations
- Security events and threats
- Authorization decisions
- Performance metrics

## Log Configuration

### Log Files

The log directory is configurable through the `LOG_BASE_DIR` environment variable (defaults to `/tmp/`):

```bash
# Default setup
python manage.py runserver  # logs to /tmp/

# Production setup
export LOG_BASE_DIR=/var/log/identity
python manage.py runserver  # logs to /var/log/identity/

# Testing with custom directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging --skip-checks
```

The following log files are created in the configured directory:

- **identity.log** - General application logs
- **identity_debug.log** - Debug level logs (development only)
- **identity_error.log** - Error and critical logs
- **identity_auth.log** - Authentication-specific logs
- **identity_security.log** - Security-related events
- **identity_jwt.log** - JWT token operations

### Log Levels

The logging configuration supports all standard Python logging levels:
- `DEBUG` - Detailed diagnostic information
- `INFO` - General information about application flow
- `WARNING` - Suspicious or unexpected activities
- `ERROR` - Authentication/authorization errors
- `CRITICAL` - Security breaches or system failures

### Loggers

The following loggers are configured:

- `identity_app` - Main application logger
- `identity_app.auth` - Authentication events
- `identity_app.security` - Security events
- `identity_app.jwt` - JWT token operations
- `identity_app.performance` - Performance metrics
- `django.request` - Django request handling
- `django.security` - Django security events

## Logging Utilities

### Available Functions

#### `log_view_access(view_name)`
Decorator for logging view access with authentication context.

```python
@log_view_access('login_page')
def login_user(request):
    return render(request, 'login.html')
```

#### `log_authentication_attempt(request, username, success, reason, user)`
Log authentication attempts with detailed context.

```python
log_authentication_attempt(
    request=request,
    username='john.doe',
    success=True,
    user=user_object
)
```

#### `log_jwt_operation(operation, username, token_data, request, success, error)`
Log JWT token operations.

```python
log_jwt_operation(
    operation='token_created',
    username='john.doe',
    token_data={'exp': 1234567890},
    request=request,
    success=True
)
```

#### `log_security_event(event_type, request, user, severity, extra_data)`
Log security-related events.

```python
log_security_event(
    event_type='suspicious_login_pattern',
    request=request,
    user=user,
    severity='WARNING',
    extra_data={'attempts': 5, 'time_window': '5min'}
)
```

#### `log_login_event(request, username, success, method, extra_data)`
Log login events with authentication method.

```python
log_login_event(
    request=request,
    username='john.doe',
    success=True,
    method='password',
    extra_data={'two_factor': True}
)
```

#### `log_logout_event(request, user)`
Log logout events.

```python
log_logout_event(request=request, user=user)
```

### StructuredLogger Classes

The identity provider includes specialized structured loggers:

```python
from identity_app.logging_utils import (
    AuthenticationLogger,
    SecurityLogger,
    JWTLogger
)

# Authentication logging
auth_logger = AuthenticationLogger('identity_app.auth.custom')
auth_logger.log_login_attempt(username='john.doe', success=True, ip='192.168.1.1')

# Security logging
security_logger = SecurityLogger('identity_app.security.custom')
security_logger.log_suspicious_activity(
    activity_type='multiple_failed_logins',
    user_id=123,
    ip='192.168.1.100'
)

# JWT logging
jwt_logger = JWTLogger('identity_app.jwt.custom')
jwt_logger.log_token_operation(
    operation='token_validated',
    username='john.doe',
    token_id='abc123'
)
```

## Testing Logging

### Management Command

Test the logging configuration using the management command:

```bash
# Test basic logging (default directory)
python manage.py test_logging --skip-checks

# Test with custom log directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging --skip-checks

# Test all loggers with custom directory
LOG_BASE_DIR=/var/log/identity python manage.py test_logging --all-loggers --skip-checks

# Test specific log level
python manage.py test_logging --level debug --skip-checks
```

### Manual Testing

```python
import logging
from identity_app.logging_utils import log_security_event

# Test standard logging
logger = logging.getLogger('identity_app')
logger.info('Test message')

# Test utility functions
log_security_event('test_event', severity='INFO')
```

## Security Event Categories

### Authentication Events
- `login_success` - Successful login
- `login_failure` - Failed login attempt
- `password_change` - Password changed
- `account_lockout` - Account locked due to failed attempts
- `account_unlock` - Account unlocked

### Authorization Events
- `permission_granted` - Permission granted
- `permission_denied` - Permission denied
- `role_assigned` - Role assigned to user
- `role_removed` - Role removed from user

### JWT Events
- `token_created` - JWT token created
- `token_validated` - JWT token validated
- `token_expired` - JWT token expired
- `token_revoked` - JWT token revoked
- `token_invalid` - Invalid JWT token

### Security Events
- `suspicious_activity` - Suspicious user activity
- `brute_force_attempt` - Brute force attack detected
- `unusual_access_pattern` - Unusual access pattern
- `security_violation` - Security policy violation

## Best Practices

### 1. Authentication Logging
Always log authentication attempts:

```python
# In authentication views
log_authentication_attempt(
    request=request,
    username=username,
    success=success,
    reason=failure_reason,
    user=user if success else None
)
```

### 2. Security Event Logging
Log all security-relevant events:

```python
# Failed login attempts
log_security_event(
    event_type='failed_login',
    request=request,
    severity='WARNING',
    extra_data={'username': username, 'attempt_count': count}
)

# Suspicious activities
log_security_event(
    event_type='suspicious_activity',
    request=request,
    user=user,
    severity='ERROR',
    extra_data={'activity_type': 'unusual_access_pattern'}
)
```

### 3. JWT Token Logging
Log JWT operations for audit trails:

```python
# Token creation
log_jwt_operation(
    operation='token_created',
    username=user.username,
    token_data={'exp': exp_timestamp},
    request=request
)

# Token validation
log_jwt_operation(
    operation='token_validated',
    username=user.username,
    request=request,
    success=True
)
```

### 4. Context Information
Include comprehensive context:
- User information (ID, username, email)
- Request details (IP, User-Agent, path)
- Session information
- Timestamps
- Relevant metadata

### 5. Security Considerations
- Never log passwords or tokens
- Log security events immediately
- Use appropriate severity levels
- Monitor logs for security incidents

## Monitoring and Alerting

### Critical Security Events
Set up immediate alerts for:
- Multiple failed login attempts
- Unusual access patterns
- Token manipulation attempts
- Privilege escalation attempts

### Authentication Monitoring
- Monitor login success/failure rates
- Track authentication method usage
- Identify suspicious login patterns
- Monitor account lockouts

### JWT Token Monitoring
- Monitor token creation/validation rates
- Track token expiration patterns
- Identify token abuse
- Monitor token revocation

## Integration with Security Tools

### SIEM Integration
The structured logging format is compatible with SIEM tools:

```json
{
  "level": "WARNING",
  "time": "2024-01-20T10:30:00Z",
  "module": "identity_app.auth",
  "event_type": "failed_login",
  "username": "john.doe",
  "ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "attempt_count": 3
}
```

### Log Analysis
Use log analysis tools to:
- Detect patterns in authentication failures
- Identify compromised accounts
- Monitor for insider threats
- Generate security reports

## Compliance and Auditing

### Audit Requirements
The logging system supports compliance with:
- SOX (Sarbanes-Oxley)
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- PCI DSS (Payment Card Industry Data Security Standard)

### Audit Trail
Maintain comprehensive audit trails for:
- User authentication events
- Authorization decisions
- Token operations
- Security events
- Administrative actions

## Configuration Details

The logging configuration is defined in `identity-provider/main/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'auth_formatter': {
            'format': '{levelname} {asctime} [AUTH] {module} {message}',
            'style': '{',
        },
        'security_formatter': {
            'format': '{levelname} {asctime} [SECURITY] {module} {message}',
            'style': '{',
        },
        'jwt_formatter': {
            'format': '{levelname} {asctime} [JWT] {module} {message}',
            'style': '{',
        },
    },
    # ... handlers and loggers configuration
}
```

## Troubleshooting

### Common Issues

1. **Authentication logs missing**: Check view decorators and function calls
2. **Security events not logged**: Verify logger names and handlers
3. **JWT logs incomplete**: Ensure token operations are properly logged
4. **Performance issues**: Monitor log file sizes and rotation

### Debug Authentication Issues

Enable debug logging for authentication:

```python
LOGGING['loggers']['identity_app.auth']['level'] = 'DEBUG'
```

### Security Investigation

For security incidents:
1. Check security logs for event timeline
2. Correlate with authentication logs
3. Review JWT token logs for token abuse
4. Analyze access patterns

## Production Deployment

### Security Considerations
- Use secure log storage
- Implement log retention policies
- Encrypt sensitive log data
- Restrict log access

### Monitoring Setup
- Real-time security event monitoring
- Automated alerting for critical events
- Log aggregation and analysis
- Regular security log reviews
