"""
Logging utilities for the website webapp.
Provides convenient logging functions and decorators.
"""
import logging
import functools
import time
from typing import Callable, Any, Optional
from django.http import HttpRequest
from django.utils import timezone

# Get logger for webapp utilities
logger = logging.getLogger('webapp.utils')


def log_user_action(action: str, user=None, extra_data: Optional[dict] = None):
    """
    Log a user action with standardized format.
    
    Args:
        action: Description of the action taken
        user: Django user object (optional)
        extra_data: Additional data to include in the log
    """
    log_data = {
        'action': action,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
    }
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': getattr(user, 'username', 'Unknown'),
            'user_email': getattr(user, 'email', 'Unknown'),
        })
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"User action: {action}", extra=log_data)


def log_performance(func_name: str, duration: float, extra_data: Optional[dict] = None):
    """
    Log performance metrics for a function or operation.
    
    Args:
        func_name: Name of the function or operation
        duration: Duration in seconds
        extra_data: Additional performance data
    """
    log_data = {
        'function': func_name,
        'duration_ms': round(duration * 1000, 2),
        'timestamp': timezone.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    # Log as warning if operation is slow
    if duration > 1.0:
        logger.warning(f"Slow operation: {func_name} took {duration:.3f}s", extra=log_data)
    else:
        logger.debug(f"Performance: {func_name} completed in {duration:.3f}s", extra=log_data)


def log_security_event(event_type: str, request: HttpRequest = None, user=None, severity: str = 'INFO', extra_data: Optional[dict] = None):
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        request: Django request object (optional)
        user: Django user object (optional)
        severity: Log level (INFO, WARNING, ERROR, CRITICAL)
        extra_data: Additional security data
    """
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
        })
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': getattr(user, 'username', 'Unknown'),
        })
    
    if extra_data:
        log_data.update(extra_data)
    
    # Get the appropriate logger level
    log_level = getattr(logging, severity.upper(), logging.INFO)
    
    security_logger = logging.getLogger('webapp.security')
    security_logger.log(log_level, f"Security event: {event_type}", extra=log_data)


def get_client_ip(request: HttpRequest) -> str:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or 'Unknown'


def log_view_access(view_name: str):
    """
    Decorator to automatically log view access.
    
    Usage:
        @log_view_access('home_page')
        def home_view(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            start_time = time.time()
            
            # Log view access
            user = getattr(request, 'user', None)
            log_user_action(
                f"Accessed {view_name}",
                user=user,
                extra_data={
                    'view_name': view_name,
                    'path': request.path,
                    'method': request.method,
                    'ip': get_client_ip(request),
                }
            )
            
            try:
                # Execute the view
                result = func(request, *args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                log_performance(
                    f"{view_name}_view",
                    duration,
                    extra_data={
                        'view_name': view_name,
                        'status': 'success',
                        'user': str(user) if user else 'Anonymous',
                    }
                )
                
                return result
                
            except Exception as e:
                # Log view errors
                duration = time.time() - start_time
                logger.error(
                    f"Error in {view_name} view: {str(e)}",
                    extra={
                        'view_name': view_name,
                        'user': str(user) if user else 'Anonymous',
                        'ip': get_client_ip(request),
                        'duration_ms': round(duration * 1000, 2),
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


class StructuredLogger:
    """
    A structured logger class for consistent logging across the webapp.
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
webapp_logger = StructuredLogger('webapp')
security_logger = StructuredLogger('webapp.security')
performance_logger = StructuredLogger('webapp.performance')
user_logger = StructuredLogger('webapp.user_actions')
