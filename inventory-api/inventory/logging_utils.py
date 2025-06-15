"""
Logging utilities for the Inventory API.
Provides convenient logging functions and decorators for inventory operations.
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
        @log_api_request('inventory_health')
        @api_view(['GET'])
        def health(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            logger = logging.getLogger('inventory.api')
            start_time = time.time()
            
            # Extract request information
            user = getattr(request, 'user', None)
            method = getattr(request, 'method', 'UNKNOWN')
            path = getattr(request, 'path', 'UNKNOWN')
            client_ip = get_client_ip(request)
            
            # Log API request start
            logger.info(
                f"INVENTORY API REQUEST START: {method} {path} - {endpoint_name}",
                extra={
                    'endpoint': endpoint_name,
                    'method': method,
                    'path': path,
                    'user': str(user) if user and user.is_authenticated else 'Anonymous',
                    'ip': client_ip,
                    'user_agent': getattr(request, 'META', {}).get('HTTP_USER_AGENT', 'Unknown'),
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
                    f"INVENTORY API REQUEST SUCCESS: {method} {path} - {endpoint_name} -> {status_code} ({duration:.3f}s)",
                    extra={
                        'endpoint': endpoint_name,
                        'method': method,
                        'path': path,
                        'status_code': status_code,
                        'duration_ms': round(duration * 1000, 2),
                        'user': str(user) if user and user.is_authenticated else 'Anonymous',
                        'ip': client_ip,
                        'timestamp': timezone.now().isoformat(),
                    }
                )
                
                # Log slow API requests
                if duration > 1.0:
                    logger.warning(
                        f"SLOW INVENTORY API REQUEST: {endpoint_name} took {duration:.3f}s",
                        extra={
                            'endpoint': endpoint_name,
                            'duration_ms': round(duration * 1000, 2),
                            'user': str(user) if user and user.is_authenticated else 'Anonymous',
                            'ip': client_ip,
                        }
                    )
                
                return result
                
            except Exception as e:
                # Log API errors
                duration = time.time() - start_time
                
                logger.error(
                    f"INVENTORY API REQUEST ERROR: {method} {path} - {endpoint_name} failed after {duration:.3f}s: {str(e)}",
                    extra={
                        'endpoint': endpoint_name,
                        'method': method,
                        'path': path,
                        'duration_ms': round(duration * 1000, 2),
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'user': str(user) if user and user.is_authenticated else 'Anonymous',
                        'ip': client_ip,
                        'timestamp': timezone.now().isoformat(),
                    },
                    exc_info=True
                )
                raise
        
        return wrapper
    return decorator


def log_inventory_operation(operation_type: str, user=None, item_id: Optional[str] = None, 
                           quantity: Optional[int] = None, extra_data: Optional[Dict[str, Any]] = None):
    """
    Log inventory-specific operations.
    
    Args:
        operation_type: Type of inventory operation (e.g., 'item_created', 'stock_updated')
        user: Django user object
        item_id: Inventory item identifier
        quantity: Quantity involved in the operation
        extra_data: Additional inventory data
    """
    logger = logging.getLogger('inventory.operations')
    
    log_data = {
        'operation_type': operation_type,
        'user': str(user) if user else 'System',
        'timestamp': timezone.now().isoformat(),
    }
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': getattr(user, 'username', 'Unknown'),
            'user_email': getattr(user, 'email', 'Unknown'),
        })
    
    if item_id is not None:
        log_data['item_id'] = item_id
    
    if quantity is not None:
        log_data['quantity'] = quantity
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"INVENTORY OPERATION: {operation_type}", extra=log_data)


def log_security_event(event_type: str, request=None, user=None, severity: str = 'INFO', 
                      extra_data: Optional[Dict[str, Any]] = None):
    """
    Log security-related events for the inventory API.
    
    Args:
        event_type: Type of security event
        request: Django/DRF request object
        user: Django user object
        severity: Log level (INFO, WARNING, ERROR, CRITICAL)
        extra_data: Additional security data
    """
    logger = logging.getLogger('inventory.security')
    
    log_data = {
        'event_type': event_type,
        'user': str(user) if user else 'Anonymous',
        'timestamp': timezone.now().isoformat(),
    }
    
    if request:
        log_data.update({
            'ip': get_client_ip(request),
            'user_agent': getattr(request, 'META', {}).get('HTTP_USER_AGENT', 'Unknown'),
            'path': getattr(request, 'path', 'Unknown'),
            'method': getattr(request, 'method', 'Unknown'),
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
    logger.log(log_level, f"INVENTORY SECURITY EVENT: {event_type}", extra=log_data)


def log_performance_metric(operation: str, duration: float, extra_data: Optional[Dict[str, Any]] = None):
    """
    Log performance metrics for inventory operations.
    
    Args:
        operation: Name of the operation
        duration: Duration in seconds
        extra_data: Additional performance data
    """
    logger = logging.getLogger('inventory.performance')
    
    log_data = {
        'operation': operation,
        'duration_ms': round(duration * 1000, 2),
        'timestamp': timezone.now().isoformat(),
    }
    
    if extra_data:
        log_data.update(extra_data)
    
    # Log as warning if operation is slow
    if duration > 1.0:
        logger.warning(f"SLOW INVENTORY OPERATION: {operation} took {duration:.3f}s", extra=log_data)
    else:
        logger.debug(f"INVENTORY PERFORMANCE: {operation} completed in {duration:.3f}s", extra=log_data)


def log_data_access(resource: str, action: str, user=None, resource_id: Optional[str] = None,
                   extra_data: Optional[Dict[str, Any]] = None):
    """
    Log data access events for compliance and auditing.
    
    Args:
        resource: Type of resource accessed (e.g., 'inventory_item', 'stock_report')
        action: Action performed (e.g., 'read', 'create', 'update', 'delete')
        user: Django user object
        resource_id: Identifier of the specific resource
        extra_data: Additional audit data
    """
    logger = logging.getLogger('inventory.audit')
    
    log_data = {
        'resource': resource,
        'action': action,
        'user': str(user) if user else 'System',
        'timestamp': timezone.now().isoformat(),
    }
    
    if user and hasattr(user, 'id'):
        log_data.update({
            'user_id': user.id,
            'username': getattr(user, 'username', 'Unknown'),
            'user_email': getattr(user, 'email', 'Unknown'),
        })
    
    if resource_id:
        log_data['resource_id'] = resource_id
    
    if extra_data:
        log_data.update(extra_data)
    
    logger.info(f"DATA ACCESS: {action.upper()} {resource}", extra=log_data)


class StructuredLogger:
    """
    A structured logger class for consistent logging across the inventory API.
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
inventory_logger = StructuredLogger('inventory')
api_logger = StructuredLogger('inventory.api')
security_logger = StructuredLogger('inventory.security')
operations_logger = StructuredLogger('inventory.operations')
audit_logger = StructuredLogger('inventory.audit')
