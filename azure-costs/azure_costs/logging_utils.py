"""
Logging utilities for the Azure Costs API.
Provides convenient logging functions and decorators for API endpoints.
"""
import logging
import functools
import time
from typing import Callable, Any, Optional, Dict
from django.http import HttpRequest
from django.utils import timezone
from rest_framework.request import Request as DRFRequest


def get_client_ip(request) -> str:
    """Extract client IP address from request."""
    # Handle both Django HttpRequest and DRF Request
    if hasattr(request, '_request'):
        # DRF Request object
        meta = request._request.META
    else:
        # Django HttpRequest
        meta = request.META
    
    x_forwarded_for = meta.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return meta.get('REMOTE_ADDR', 'Unknown')


def log_api_request(endpoint_name: str):
    """
    Decorator to automatically log API endpoint access and performance.
    
    Usage:
        @log_api_request('health_check')
        @api_view(['GET'])
        def health(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            logger = logging.getLogger('azure_costs.api')
            start_time = time.time()
            
            # Extract request information
            user = getattr(request, 'user', None)
            method = getattr(request, 'method', 'UNKNOWN')
            path = getattr(request, 'path', 'UNKNOWN')
            client_ip = get_client_ip(request)
            
            # Log API request start
            logger.info(
                f"API Request started: {endpoint_name} - {method} {path}",
                extra={
                    'endpoint': endpoint_name,
                    'method': method,
                    'path': path,
                    'user': str(user) if user and user.is_authenticated else 'Anonymous',
                    'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
                    'ip': client_ip,
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            try:
                # Execute the API endpoint
                result = func(request, *args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                status_code = getattr(result, 'status_code', 200)
                
                logger.info(
                    f"API Request completed: {endpoint_name} - Status: {status_code}, Duration: {duration:.3f}s",
                    extra={
                        'endpoint': endpoint_name,
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'duration': duration,
                        'user': str(user) if user and user.is_authenticated else 'Anonymous',
                        'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
                        'ip': client_ip,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                # Log slow API requests
                if duration > 1.0:
                    logger.warning(
                        f"Slow API request detected: {endpoint_name} - Duration: {duration:.3f}s",
                        extra={
                            'endpoint': endpoint_name,
                            'duration': duration,
                            'user': str(user) if user and user.is_authenticated else 'Anonymous',
                            'ip': client_ip,
                        }
                    )
                
                return result
                
            except Exception as e:
                # Log API errors
                duration = time.time() - start_time
                
                logger.error(
                    f"API Request failed: {endpoint_name} - Error: {str(e)}",
                    extra={
                        'endpoint': endpoint_name,
                        'method': method,
                        'path': path,
                        'duration': duration,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'user': str(user) if user and user.is_authenticated else 'Anonymous',
                        'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
                        'ip': client_ip,
                        'timestamp': timezone.now().isoformat(),
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_azure_cost_event(
    request: HttpRequest,
    event_type: str,
    resource_id: Optional[str] = None,
    cost_amount: Optional[float] = None,
    currency: str = 'USD',
    details: Optional[Dict[str, Any]] = None
):
    """
    Log Azure cost-related events.
    
    Args:
        request: Django/DRF request object
        event_type: Type of cost event (e.g., 'cost_retrieved', 'budget_exceeded')
        resource_id: Azure resource ID
        cost_amount: Cost amount
        currency: Currency code
        details: Additional event details
    """
    logger = logging.getLogger('azure_costs')
    
    user = getattr(request, 'user', None)
    log_data = {
        'event_type': event_type,
        'user': str(user) if user and user.is_authenticated else 'Anonymous',
        'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
        'ip': get_client_ip(request),
        'timestamp': timezone.now().isoformat(),
    }
    
    if resource_id:
        log_data['resource_id'] = resource_id
    
    if cost_amount is not None:
        log_data['cost_amount'] = cost_amount
        log_data['currency'] = currency
    
    if details:
        log_data.update(details)
    
    logger.info(f"Azure Cost Event: {event_type}", extra=log_data)


def log_security_event(
    request: HttpRequest,
    event_type: str,
    severity: str = 'info',
    details: Optional[Dict[str, Any]] = None
):
    """
    Log security-related events.
    
    Args:
        request: Django/DRF request object
        event_type: Type of security event
        severity: Log severity (info, warning, error, critical)
        details: Additional security details
    """
    logger = logging.getLogger('azure_costs.security')
    
    user = getattr(request, 'user', None)
    log_data = {
        'event_type': event_type,
        'user': str(user) if user and user.is_authenticated else 'Anonymous',
        'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
        'ip': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        'path': getattr(request, 'path', 'Unknown'),
        'method': getattr(request, 'method', 'Unknown'),
        'timestamp': timezone.now().isoformat(),
    }
    
    if details:
        log_data.update(details)
    
    # Get the appropriate log level
    log_level = getattr(logging, severity.upper(), logging.INFO)
    logger.log(log_level, f"Security Event: {event_type}", extra=log_data)


def log_performance_metric(
    request: HttpRequest,
    metric_name: str,
    value: float,
    unit: str = 'seconds',
    details: Optional[Dict[str, Any]] = None
):
    """
    Log performance metrics.
    
    Args:
        request: Django/DRF request object
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        details: Additional metric details
    """
    logger = logging.getLogger('azure_costs.performance')
    
    user = getattr(request, 'user', None)
    log_data = {
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'user': str(user) if user and user.is_authenticated else 'Anonymous',
        'user_id': getattr(user, 'id', None) if user and user.is_authenticated else None,
        'timestamp': timezone.now().isoformat(),
    }
    
    if details:
        log_data.update(details)
    
    # Log as warning if performance is poor
    if unit == 'seconds' and value > 1.0:
        logger.warning(f"Performance Metric: {metric_name} = {value} {unit} (slow)", extra=log_data)
    else:
        logger.info(f"Performance Metric: {metric_name} = {value} {unit}", extra=log_data)


class StructuredLogger:
    """
    A structured logger class for consistent logging across the Azure Costs API.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def info(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log an info message with structured data."""
        self.logger.info(message, extra=data or {})
    
    def warning(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a warning message with structured data."""
        self.logger.warning(message, extra=data or {})
    
    def error(self, message: str, data: Optional[Dict[str, Any]] = None, exc_info: bool = False):
        """Log an error message with structured data."""
        self.logger.error(message, extra=data or {}, exc_info=exc_info)
    
    def debug(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a debug message with structured data."""
        self.logger.debug(message, extra=data or {})
    
    def critical(self, message: str, data: Optional[Dict[str, Any]] = None):
        """Log a critical message with structured data."""
        self.logger.critical(message, extra=data or {})


# Pre-configured loggers for common use cases
azure_costs_logger = StructuredLogger('azure_costs')
api_logger = StructuredLogger('azure_costs.api')
security_logger = StructuredLogger('azure_costs.security')
performance_logger = StructuredLogger('azure_costs.performance')