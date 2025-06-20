# Identity Provider Django Project Logging Documentation

## Introduction

The Identity Provider Django project implements a comprehensive logging solution specifically designed for authentication, authorization, and RBAC/ABAC operations. The logging system provides specialized security event tracking, authentication monitoring, JWT operations logging, and role-based access control auditing.

### Overall Configuration

The logging configuration is defined in `main/settings.py` and includes:

- **Log Base Directory**: Configurable via `LOG_BASE_DIR` environment variable (defaults to `/tmp`)

- **Multiple Log Files**:
  - `identity_provider.log` - General application logs (10MB max, 5 backups)
  - `identity_provider_debug.log` - Debug information (10MB max, 3 backups, only in DEBUG mode)
  - `identity_provider_errors.log` - Error logs (5MB max, 10 backups)
  - `identity_provider_auth.log` - Authentication events (10MB max, 5 backups)
  - `identity_provider_security.log` - Security events (5MB max, 10 backups)

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Formatters**: verbose, simple, detailed, security
- **Automatic Rotation**: Prevents log files from consuming excessive disk space

### Key Components

1. **Logging Utilities** (`identity_app/logging_utils.py`):
   - Helper functions for authentication, JWT, and security logging
   - `@log_view_access` decorator for automatic view logging
   - StructuredLogger class for consistent logging
   - Pre-configured loggers for different concerns

2. **Specialized Loggers**:
   - Authentication logger for login/logout events
   - Security logger for security violations and suspicious activities
   - JWT logger for token operations
   - RBAC/ABAC logger for role and attribute operations

## How to Add Logging to Django Apps

### 1. Import the Required Utilities

In your Django app's views, models, or any Python file:

```python
from identity_app.logging_utils import (
    log_view_access,
    log_authentication_attempt,
    log_jwt_operation,
    log_security_event,
    log_login_event,
    log_logout_event,
    get_client_ip
)
```

### 2. Use the View Access Decorator

For automatic view logging with timing:

```python
from identity_app.logging_utils import log_view_access

@log_view_access
def my_view(request):
    # Your view logic here
    return JsonResponse({'status': 'success'})
```

This automatically logs:
- View entry with request details
- View exit with response status
- Execution time in milliseconds
- Any exceptions that occur

### 3. Log Authentication Events

For authentication-related operations:

```python
from identity_app.logging_utils import log_authentication_attempt, log_login_event

def login_view(request):
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    # Log the authentication attempt
    log_authentication_attempt(
        request,
        username=username,
        success=False,  # Will be updated based on result
        reason='attempting_authentication'
    )
    
    user = authenticate(username=username, password=password)
    
    if user:
        login(request, user)
        # Log successful login
        log_login_event(request, user, 'local')
        log_authentication_attempt(
            request,
            username=username,
            success=True,
            user_id=user.id
        )
        return redirect('dashboard')
    else:
        # Log failed login
        log_authentication_attempt(
            request,
            username=username,
            success=False,
            reason='invalid_credentials'
        )
        return render(request, 'login.html', {'error': 'Invalid credentials'})
```

### 4. Log JWT Operations

For JWT token management:

```python
from identity_app.logging_utils import log_jwt_operation

def create_token(user, request):
    # Generate JWT token
    token = generate_jwt_token(user)
    
    # Log token creation
    log_jwt_operation(
        request,
        operation='token_created',
        user_id=user.id,
        details={
            'token_type': 'access',
            'expires_in': 3600,
            'scopes': ['read', 'write']
        }
    )
    
    return token

def validate_token(token, request):
    try:
        payload = decode_jwt_token(token)
        log_jwt_operation(
            request,
            operation='token_validated',
            user_id=payload.get('user_id'),
            details={'token_type': 'access'}
        )
        return payload
    except TokenExpiredError:
        log_jwt_operation(
            request,
            operation='token_expired',
            details={'token': token[:20] + '...'}
        )
        raise
    except InvalidTokenError:
        log_jwt_operation(
            request,
            operation='token_invalid',
            details={'reason': 'signature_verification_failed'}
        )
        raise
```

### 5. Log Security Events

For security-related incidents:

```python
from identity_app.logging_utils import log_security_event

def sensitive_operation(request):
    # Check for suspicious activity
    if is_brute_force_attempt(request):
        log_security_event(
            request,
            event_type='brute_force_attempt',
            severity='high',
            details={
                'ip': get_client_ip(request),
                'attempts': get_failed_attempts(request),
                'timeframe': '5_minutes'
            }
        )
        return HttpResponse('Too many attempts', status=429)
    
    # Check permissions
    if not user_has_permission(request.user, 'admin'):
        log_security_event(
            request,
            event_type='permission_denied',
            severity='medium',
            details={
                'user_id': request.user.id,
                'required_permission': 'admin',
                'attempted_action': 'access_admin_panel'
            }
        )
        return HttpResponseForbidden()
```

### 6. Log RBAC/ABAC Operations

For role and attribute management:

```python
import logging

logger = logging.getLogger('identity_app')

def assign_role(user, role, assigned_by):
    # Assign role logic
    user_role = UserRole.objects.create(user=user, role=role)
    
    # Log role assignment
    logger.info(f"Role assigned", extra={
        'event': 'role_assigned',
        'user_id': user.id,
        'role': role.name,
        'assigned_by': assigned_by.id,
        'timestamp': timezone.now().isoformat()
    })
    
    # Also log as security event
    log_security_event(
        request=None,  # If not in request context
        event_type='role_assigned',
        severity='info',
        details={
            'user_id': user.id,
            'role': role.name,
            'assigned_by_id': assigned_by.id
        }
    )

def set_user_attribute(user, attribute_name, attribute_value):
    # Set attribute logic
    attribute = UserAttribute.objects.update_or_create(
        user=user,
        name=attribute_name,
        defaults={'value': attribute_value}
    )
    
    # Log attribute change
    logger.info(f"User attribute updated", extra={
        'event': 'attribute_updated',
        'user_id': user.id,
        'attribute': attribute_name,
        'new_value': attribute_value,
        'timestamp': timezone.now().isoformat()
    })
```

### 7. Service Registration Logging

For RBAC manifest registration:

```python
def register_service_manifest(service_name, manifest_data):
    logger = logging.getLogger('identity_app')
    
    logger.info(f"Service registering RBAC manifest", extra={
        'service': service_name,
        'roles_count': len(manifest_data.get('roles', [])),
        'permissions_count': len(manifest_data.get('permissions', [])),
        'timestamp': timezone.now().isoformat()
    })
    
    # Process manifest...
    
    logger.info(f"Service RBAC manifest registered successfully", extra={
        'service': service_name,
        'timestamp': timezone.now().isoformat()
    })
```

## Request Flow Tracking

The logging system enables tracking authentication and authorization flows:

### 1. Request Context

Every log entry includes:
- **User Information**: User ID, username, email (when available)
- **Request Details**: HTTP method, path, query parameters
- **Client Information**: IP address (with X-Forwarded-For support), user agent
- **Session Information**: Session key for tracking authentication sessions
- **Timestamps**: ISO format timestamps for chronological ordering

### 2. Authentication Flow

A typical authentication flow appears in logs as:

```
# 1. Login attempt (identity_provider_auth.log)
2024-01-20 10:30:00,123 INFO [identity_app.auth] Authentication attempt - Username: john_doe, IP: 192.168.1.100, User-Agent: Mozilla/5.0...

# 2. Login success (identity_provider_auth.log)
2024-01-20 10:30:00,200 INFO [identity_app.login] Login successful - User: john_doe (123), Method: local, IP: 192.168.1.100

# 3. JWT token creation (identity_provider.log)
2024-01-20 10:30:00,210 INFO [identity_app] JWT operation: token_created - User: 123, Details: {'token_type': 'access', 'expires_in': 3600}

# 4. Role check (identity_provider.log)
2024-01-20 10:30:00,220 INFO [identity_app] User roles loaded from cache - User: 123, Roles: ['user', 'admin']

# 5. Attribute loading (identity_provider.log)
2024-01-20 10:30:00,225 INFO [identity_app] User attributes loaded from Redis - User: 123, Load time: 5ms

# 6. View access (identity_provider.log)
2024-01-20 10:30:00,230 INFO [identity_app.views] View accessed: dashboard - User: john_doe, Duration: 107ms
```

### 3. Following a User Session

To track a complete user session:

1. **Track login to logout**:
   ```bash
   # Find user's login
   grep "Login successful.*User: john_doe" /tmp/identity_provider_auth.log
   
   # Track all activities for that session
   SESSION_KEY="abc123..."  # From login log
   grep "$SESSION_KEY" /tmp/identity_provider*.log | sort -k2
   
   # Find logout
   grep "Logout.*User: john_doe" /tmp/identity_provider_auth.log
   ```

2. **Track JWT token lifecycle**:
   ```bash
   # Token creation
   grep "token_created.*User: 123" /tmp/identity_provider.log
   
   # Token validations
   grep "token_validated.*User: 123" /tmp/identity_provider.log
   
   # Token expiration or revocation
   grep "token_expired\|token_revoked.*User: 123" /tmp/identity_provider.log
   ```

3. **Monitor security events**:
   ```bash
   # Failed login attempts
   grep "Authentication attempt.*success\": false" /tmp/identity_provider_auth.log
   
   # Security violations
   tail -f /tmp/identity_provider_security.log | grep "severity.*high"
   
   # Permission denials
   grep "permission_denied" /tmp/identity_provider_security.log
   ```

### 4. Debugging Tips

1. **Enable DEBUG logging** for development:
   ```python
   # In settings.py
   LOGGING['loggers']['identity_app']['level'] = 'DEBUG'
   LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'
   ```

2. **Track RBAC/ABAC operations**:
   ```bash
   # Role assignments
   grep "role_assigned\|role_removed" /tmp/identity_provider*.log
   
   # Attribute changes
   grep "attribute_updated" /tmp/identity_provider.log
   
   # Cache operations
   grep "cache_invalidated\|cache_populated" /tmp/identity_provider.log
   ```

3. **Monitor service registrations**:
   ```bash
   # Service manifest registrations
   grep "Service registering RBAC manifest" /tmp/identity_provider.log
   
   # CORS discovery
   grep "CORS.*discovered" /tmp/identity_provider.log
   ```

4. **Create correlation for distributed operations**:
   ```python
   import uuid
   
   def distributed_auth_flow(request):
       correlation_id = str(uuid.uuid4())
       logger = logging.getLogger('identity_app')
       
       # Log start of flow
       logger.info("Starting distributed auth flow", extra={
           'correlation_id': correlation_id,
           'user': request.user.username,
           'services': ['billing', 'inventory']
       })
       
       # Pass correlation_id to other services
       for service in ['billing', 'inventory']:
           verify_service_access(service, correlation_id)
       
       logger.info("Distributed auth flow completed", extra={
           'correlation_id': correlation_id,
           'duration': calculate_duration()
       })
   ```

## Security Event Categories

The identity provider logs these security event types:

### Authentication Events
- `login_success` - Successful login
- `login_failure` - Failed login attempt
- `logout` - User logout
- `password_change` - Password modification
- `password_reset` - Password reset request
- `account_lockout` - Account locked due to failed attempts

### Authorization Events
- `permission_granted` - Access granted to resource
- `permission_denied` - Access denied to resource
- `role_assigned` - Role assigned to user
- `role_removed` - Role removed from user
- `attribute_set` - User attribute modified

### JWT Events
- `token_created` - New JWT token issued
- `token_validated` - Token successfully validated
- `token_expired` - Token expiration detected
- `token_revoked` - Token manually revoked
- `token_invalid` - Invalid token presented

### Security Violations
- `brute_force_attempt` - Multiple failed login attempts
- `suspicious_activity` - Unusual access patterns
- `unauthorized_access` - Attempt to access restricted resource
- `security_violation` - General security policy violation

## Best Practices

1. **Use specialized logging functions** for consistency:
   - `log_authentication_attempt()` for all auth attempts
   - `log_jwt_operation()` for all token operations
   - `log_security_event()` for security incidents

2. **Include complete context** in security logs:
   - User identification (ID, username)
   - Client information (IP, user agent)
   - Timestamp and session information
   - Specific reason for security events

3. **Use appropriate severity levels** for security events:
   - `info` - Normal operations (successful login)
   - `warning` - Notable events (permission denial)
   - `high` - Security threats (brute force attempts)
   - `critical` - Severe violations requiring immediate action

4. **Monitor authentication patterns**:
   - Failed login attempts per user/IP
   - Unusual login times or locations
   - Rapid role/permission changes
   - Token abuse patterns

5. **Maintain audit trails**:
   - Log all privilege escalations
   - Track all RBAC/ABAC changes
   - Record service manifest updates
   - Keep security logs for compliance

## Log File Management

1. **Rotation Strategy**:
   - Auth logs: 10MB max, 5 backups (high volume)
   - Security logs: 5MB max, 10 backups (critical retention)
   - Error logs: 5MB max, 10 backups
   - General logs: 10MB max, 5 backups

2. **Security Considerations**:
   - Store security logs separately
   - Implement access controls on log files
   - Consider encryption for sensitive logs
   - Regular backup of security/audit logs

3. **Monitoring Recommendations**:
   - Alert on high severity security events
   - Monitor authentication failure rates
   - Track JWT token anomalies
   - Watch for privilege escalation patterns