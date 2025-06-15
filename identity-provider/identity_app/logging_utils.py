"""
Logging utilities for the Identity Provider.
Provides comprehensive logging for authentication, security, and JWT operations.
"""
import logging
import functools
import time
from typing import Callable, Any, Optional, Dict
from django.http import HttpRequest
from django.utils import timezone
from django.contrib.auth.models import User


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'Unknown')


def log_view_access(view_name: str):
    """
    Decorator to automatically log view access with authentication context.
    
    Usage:
        @log_view_access('login_page')
        def login_user(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            logger = logging.getLogger('identity_app.views')
            start_time = time.time()
            
            # Log view access
            logger.info(
                f"VIEW ACCESS: {view_name}",
                extra={
                    'view_name': view_name,
                    'method': request.method,
                    'path': request.path,
                    'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                    'ip': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            try:
                # Execute the view
                result = func(request, *args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                status_code = getattr(result, 'status_code', 200)
                
                logger.info(
                    f"VIEW SUCCESS: {view_name} -> {status_code} ({duration:.3f}s)",
                    extra={
                        'view_name': view_name,
                        'status_code': status_code,
                        'duration_ms': round(duration * 1000, 2),
                        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                        'ip': get_client_ip(request),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                return result
                
            except Exception as e:
                # Log view errors
                duration = time.time() - start_time
                
                logger.error(
                    f"VIEW ERROR: {view_name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        'view_name': view_name,
                        'duration_ms': round(duration * 1000, 2),
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                        'ip': get_client_ip(request),
                        'timestamp': timezone.now().isoformat(),
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_authentication_attempt(request: HttpRequest, username: str, success: bool, 
                             reason: str = None, user: User = None):
    """
    Log authentication attempts with detailed context.
    
    Args:
        request: Django request object
        username: Username attempting authentication
        success: Whether authentication was successful
        reason: Reason for failure (if applicable)
        user: User object (if authentication successful)
    """
    logger = logging.getLogger('identity_app.auth')
    
    log_data = {
        'username': username,
        'success': success,
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'referer': request.META.get('HTTP_REFERER', ''),
        'timestamp': timezone.now().isoformat(),
        'session_key': request.session.session_key or 'No session',
    }
    
    if user:
        log_data.update({
            'user_id': user.id,
            'user_email': user.email,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        })
    
    if reason:
        log_data['failure_reason'] = reason
    
    if success:
        logger.info(f"AUTH SUCCESS: {username}", extra=log_data)
    else:
        logger.warning(f"AUTH FAILED: {username} - {reason or 'Unknown reason'}", extra=log_data)


def log_jwt_operation(operation: str, username: str = None, token_data: Dict[str, Any] = None,
                     request: HttpRequest = None, success: bool = True, error: str = None):
    """
    Log JWT token operations (creation, validation, etc.).
    
    Args:
        operation: Type of JWT operation (e.g., 'token_created', 'token_validated')
        username: Username associated with the token
        token_data: JWT payload data (sensitive data will be filtered)
        request: Django request object
        success: Whether the operation was successful
        error: Error message if operation failed
    """
    logger = logging.getLogger('identity_app.auth')
    
    log_data = {
        'operation': operation,
        'username': username or 'Unknown',
        'success': success,
        'timestamp': timezone.now().isoformat(),
    }
    
    if request:
        log_data.update({
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'referer': request.META.get('HTTP_REFERER', ''),
        })
    
    if token_data:
        # Filter sensitive data from token payload
        filtered_data = {k: v for k, v in token_data.items() 
                        if k not in ['password', 'secret', 'key']}
        log_data['token_payload'] = filtered_data
    
    if error:
        log_data['error'] = error
    
    if success:
        logger.info(f"JWT {operation.upper()}: {username or 'Unknown'}", extra=log_data)
    else:
        logger.error(f"JWT {operation.upper()} FAILED: {error}", extra=log_data)


def log_security_event(event_type: str, request: HttpRequest = None, user: User = None, 
                      severity: str = 'INFO', details: Dict[str, Any] = None):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        request: Django request object
        user: Django user object
        severity: Log level (INFO, WARNING, ERROR, CRITICAL)
        details: Additional security details
    """
    logger = logging.getLogger('identity_app.security')
    
    log_data = {
        'event_type': event_type,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
    }
    
    if request:
        log_data.update({
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'path': request.path,
            'method': request.method,
            'referer': request.META.get('HTTP_REFERER', ''),
        })
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': user.username,
            'user_email': user.email,
        })
    
    if details:
        log_data.update(details)
    
    # Get appropriate log level
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(log_level, f"SECURITY EVENT: {event_type}", extra=log_data)


def log_login_event(request: HttpRequest, username: str, success: bool, 
                   redirect_uri: str = None, user: User = None):
    """
    Log login events with SSO context.
    
    Args:
        request: Django request object
        username: Username attempting login
        success: Whether login was successful
        redirect_uri: Redirect URI for SSO
        user: User object if login successful
    """
    logger = logging.getLogger('identity_app.login')
    
    log_data = {
        'username': username,
        'success': success,
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'referer': request.META.get('HTTP_REFERER', ''),
        'redirect_uri': redirect_uri or 'Default',
        'timestamp': timezone.now().isoformat(),
        'session_key': request.session.session_key or 'No session',
    }
    
    if user:
        log_data.update({
            'user_id': user.id,
            'user_email': user.email,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
        })
    
    if success:
        logger.info(f"LOGIN SUCCESS: {username} -> {redirect_uri or 'Default'}", extra=log_data)
        
        # Also log as security event for successful logins
        log_security_event(
            'successful_login',
            request=request,
            user=user,
            severity='INFO',
            details={'redirect_uri': redirect_uri}
        )
    else:
        logger.warning(f"LOGIN FAILED: {username}", extra=log_data)
        
        # Log as security event for failed logins
        log_security_event(
            'failed_login',
            request=request,
            severity='WARNING',
            details={'attempted_username': username, 'redirect_uri': redirect_uri}
        )


def log_logout_event(request: HttpRequest, user: User = None):
    """
    Log logout events.
    
    Args:
        request: Django request object
        user: User object if available
    """
    logger = logging.getLogger('identity_app.logout')
    
    log_data = {
        'user': str(user) if user else 'Anonymous',
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'referer': request.META.get('HTTP_REFERER', ''),
        'timestamp': timezone.now().isoformat(),
        'session_key': request.session.session_key or 'No session',
    }
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': user.username,
            'user_email': user.email,
        })
    
    logger.info(f"LOGOUT: {str(user) if user else 'Anonymous'}", extra=log_data)
    
    # Also log as security event
    log_security_event(
        'user_logout',
        request=request,
        user=user,
        severity='INFO'
    )


class StructuredLogger:
    """
    A structured logger class for consistent logging across the identity provider.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, **kwargs):
        """Log an info message with structured data."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log a warning message with structured data."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log an error message with structured data."""
        self.logger.error(message, extra=kwargs, exc_info=exc_info)
    
    def debug(self, message: str, **kwargs):
        """Log a debug message with structured data."""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log a critical message with structured data."""
        self.logger.critical(message, extra=kwargs)


# Pre-configured loggers for common use cases
identity_logger = StructuredLogger('identity_app')
auth_logger = StructuredLogger('identity_app.auth')
security_logger = StructuredLogger('identity_app.security')
login_logger = StructuredLogger('identity_app.login')
logout_logger = StructuredLogger('identity_app.logout')
