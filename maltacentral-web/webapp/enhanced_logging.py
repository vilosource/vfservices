"""
Enhanced logging utilities for the Django website.
Provides additional logging features for debugging and monitoring.
"""

import logging
import functools
import time
import json
from typing import Any, Dict, Optional, Callable
from django.http import HttpRequest
from django.utils import timezone
from django.conf import settings


class RequestLogger:
    """Logger specifically for HTTP requests with enhanced context."""
    
    def __init__(self, name: str = 'webapp.requests'):
        self.logger = logging.getLogger(name)
    
    def log_request_start(self, request: HttpRequest, view_name: str = None):
        """Log the start of request processing."""
        context = self._extract_request_context(request)
        context.update({
            'event': 'request_start',
            'view_name': view_name,
            'timestamp': timezone.now().isoformat(),
        })
        
        self.logger.info(
            f"REQUEST START: {request.method} {request.path}",
            extra=context
        )
    
    def log_request_end(self, request: HttpRequest, response_status: int, duration: float, view_name: str = None):
        """Log the end of request processing."""
        context = self._extract_request_context(request)
        context.update({
            'event': 'request_end',
            'view_name': view_name,
            'response_status': response_status,
            'duration_ms': round(duration * 1000, 2),
            'timestamp': timezone.now().isoformat(),
        })
        
        log_level = logging.INFO
        if response_status >= 500:
            log_level = logging.ERROR
        elif response_status >= 400:
            log_level = logging.WARNING
        
        self.logger.log(
            log_level,
            f"REQUEST END: {request.method} {request.path} -> {response_status} ({duration:.3f}s)",
            extra=context
        )
    
    def _extract_request_context(self, request: HttpRequest) -> Dict[str, Any]:
        """Extract useful context from the request."""
        return {
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
            'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'referer': request.META.get('HTTP_REFERER', ''),
            'content_type': request.META.get('CONTENT_TYPE', ''),
            'session_key': getattr(request.session, 'session_key', None) if hasattr(request, 'session') else None,
        }
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')


class ViewLogger:
    """Enhanced view logging with automatic timing and context."""
    
    def __init__(self, name: str = 'webapp.views'):
        self.logger = logging.getLogger(name)
        self.request_logger = RequestLogger()
    
    def log_view_execution(self, view_name: str, request: HttpRequest, **kwargs):
        """Decorator to log view execution with timing."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                # Log view start
                self.request_logger.log_request_start(request, view_name)
                self.logger.debug(
                    f"VIEW START: {view_name}",
                    extra={
                        'view_name': view_name,
                        'function': func.__name__,
                        'args_count': len(args),
                        'kwargs_count': len(kwargs),
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful completion
                    duration = time.time() - start_time
                    status_code = getattr(result, 'status_code', 200)
                    
                    self.request_logger.log_request_end(request, status_code, duration, view_name)
                    self.logger.info(
                        f"VIEW SUCCESS: {view_name} completed in {duration:.3f}s",
                        extra={
                            'view_name': view_name,
                            'function': func.__name__,
                            'duration_ms': round(duration * 1000, 2),
                            'status_code': status_code,
                            'timestamp': timezone.now().isoformat(),
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    # Log view failure
                    duration = time.time() - start_time
                    
                    self.request_logger.log_request_end(request, 500, duration, view_name)
                    self.logger.error(
                        f"VIEW ERROR: {view_name} failed after {duration:.3f}s: {str(e)}",
                        extra={
                            'view_name': view_name,
                            'function': func.__name__,
                            'duration_ms': round(duration * 1000, 2),
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            'timestamp': timezone.now().isoformat(),
                        },
                        exc_info=True
                    )
                    raise
            
            return wrapper
        return decorator


class DatabaseLogger:
    """Logger for database operations."""
    
    def __init__(self, name: str = 'webapp.database'):
        self.logger = logging.getLogger(name)
    
    def log_query(self, query: str, params: Optional[tuple] = None, duration: Optional[float] = None):
        """Log database query execution."""
        context = {
            'query': query,
            'params': params,
            'timestamp': timezone.now().isoformat(),
        }
        
        if duration is not None:
            context['duration_ms'] = round(duration * 1000, 2)
        
        if duration and duration > 0.1:  # Log slow queries
            self.logger.warning(
                f"SLOW QUERY: {query[:100]}... took {duration:.3f}s",
                extra=context
            )
        else:
            self.logger.debug(
                f"QUERY: {query[:100]}...",
                extra=context
            )


class SecurityLogger:
    """Enhanced security event logging."""
    
    def __init__(self, name: str = 'webapp.security'):
        self.logger = logging.getLogger(name)
    
    def log_auth_attempt(self, request: HttpRequest, username: str, success: bool):
        """Log authentication attempts."""
        context = {
            'event': 'auth_attempt',
            'username': username,
            'success': success,
            'ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
        
        if success:
            self.logger.info(f"AUTH SUCCESS: {username}", extra=context)
        else:
            self.logger.warning(f"AUTH FAILED: {username}", extra=context)
    
    def log_permission_denied(self, request: HttpRequest, resource: str, reason: str = None):
        """Log permission denial events."""
        context = {
            'event': 'permission_denied',
            'resource': resource,
            'reason': reason,
            'user': str(request.user) if hasattr(request, 'user') else 'Unknown',
            'ip': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        self.logger.warning(f"PERMISSION DENIED: {resource}", extra=context)
    
    def log_suspicious_activity(self, request: HttpRequest, activity: str, severity: str = 'medium'):
        """Log suspicious activity."""
        context = {
            'event': 'suspicious_activity',
            'activity': activity,
            'severity': severity,
            'user': str(request.user) if hasattr(request, 'user') else 'Unknown',
            'ip': self._get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        }
        
        log_level = logging.WARNING
        if severity == 'high':
            log_level = logging.ERROR
        elif severity == 'critical':
            log_level = logging.CRITICAL
        
        self.logger.log(log_level, f"SUSPICIOUS: {activity}", extra=context)
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')


# Global logger instances
request_logger = RequestLogger()
view_logger = ViewLogger()
database_logger = DatabaseLogger()
security_logger = SecurityLogger()


def enhanced_log_view(view_name: str):
    """Enhanced view logging decorator."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            return view_logger.log_view_execution(view_name, request)(func)(request, *args, **kwargs)
        return wrapper
    return decorator


def log_database_queries(func: Callable) -> Callable:
    """Decorator to log database queries for a view."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        from django.db import connection
        
        # Get initial query count
        initial_queries = len(connection.queries)
        
        result = func(*args, **kwargs)
        
        # Log new queries
        new_queries = connection.queries[initial_queries:]
        for query in new_queries:
            database_logger.log_query(
                query['sql'],
                duration=float(query['time'])
            )
        
        if len(new_queries) > 10:  # Warn about N+1 queries
            database_logger.logger.warning(
                f"HIGH QUERY COUNT: {func.__name__} executed {len(new_queries)} queries",
                extra={
                    'function': func.__name__,
                    'query_count': len(new_queries),
                    'timestamp': timezone.now().isoformat(),
                }
            )
        
        return result
    return wrapper
