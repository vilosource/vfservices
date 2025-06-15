"""
Custom logging middleware for the website app.
Logs request/response details for monitoring and debugging.
"""
import logging
import time
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpRequest, HttpResponse
from typing import Callable, Optional
from django.http import HttpResponseRedirect

logger = logging.getLogger('webapp.middleware')


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all incoming requests and responses."""
    
    def process_request(self, request: HttpRequest) -> None:
        """Log incoming request details."""
        # Store start time for performance logging
        request._logging_start_time = time.time()
        
        # Extract useful request information
        client_ip = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
        
        # Log basic request info
        logger.info(
            f"Incoming {request.method} request to {request.path}",
            extra={
                'method': request.method,
                'path': request.path,
                'query_string': request.META.get('QUERY_STRING', ''),
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
                'ip': client_ip,
                'user_agent': user_agent,
                'content_type': request.META.get('CONTENT_TYPE', ''),
                'content_length': request.META.get('CONTENT_LENGTH', '0'),
                'referer': request.META.get('HTTP_REFERER', ''),
            }
        )
        
        # Log request body for non-GET requests (be careful with sensitive data)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body.decode('utf-8'))
                    # Filter out sensitive fields
                    filtered_body = self._filter_sensitive_data(body)
                    logger.debug(
                        f"Request body: {json.dumps(filtered_body)}",
                        extra={
                            'method': request.method,
                            'path': request.path,
                            'body': filtered_body,
                        }
                    )
                elif request.POST:
                    # Filter sensitive POST data
                    filtered_post = self._filter_sensitive_data(dict(request.POST))
                    logger.debug(
                        f"POST data: {json.dumps(filtered_post)}",
                        extra={
                            'method': request.method,
                            'path': request.path,
                            'post_data': filtered_post,
                        }
                    )
            except Exception as e:
                logger.warning(f"Could not log request body: {str(e)}")
    
    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Log response details and request duration."""
        # Calculate request duration
        start_time = getattr(request, '_logging_start_time', time.time())
        duration = time.time() - start_time
        
        # Extract response information
        client_ip = self._get_client_ip(request)
        status_code = response.status_code
        
        # Determine log level based on status code
        if status_code >= 500:
            log_level = logging.ERROR
        elif status_code >= 400:
            log_level = logging.WARNING
        else:
            log_level = logging.INFO
        
        logger.log(
            log_level,
            f"Response {status_code} for {request.method} {request.path} in {duration:.3f}s",
            extra={
                'method': request.method,
                'path': request.path,
                'status_code': status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
                'ip': client_ip,
                'response_size': len(response.content) if hasattr(response, 'content') else 0,
                'content_type': response.get('Content-Type', ''),
            }
        )
        
        # Log slow requests
        if duration > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request detected: {request.method} {request.path} took {duration:.3f}s",
                extra={
                    'method': request.method,
                    'path': request.path,
                    'duration_ms': round(duration * 1000, 2),
                    'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
                    'ip': client_ip,
                }
            )
        
        return response
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Log unhandled exceptions."""
        client_ip = self._get_client_ip(request)
        
        logger.error(
            f"Unhandled exception in {request.method} {request.path}: {str(exception)}",
            extra={
                'method': request.method,
                'path': request.path,
                'user': str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous',
                'ip': client_ip,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
            },
            exc_info=True
        )
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'Unknown'
    
    def _filter_sensitive_data(self, data: dict) -> dict:
        """Filter out sensitive data from logs."""
        if not isinstance(data, dict):
            return data
        
        sensitive_fields = {
            'password', 'passwd', 'pwd', 'secret', 'token', 'key', 
            'authorization', 'auth', 'csrf', 'ssn', 'social_security',
            'credit_card', 'card_number', 'cvv', 'pin'
        }
        
        filtered = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(sensitive in key_lower for sensitive in sensitive_fields):
                filtered[key] = '[FILTERED]'
            elif isinstance(value, dict):
                filtered[key] = self._filter_sensitive_data(value)
            else:
                filtered[key] = value
        
        return filtered


class LoginRequiredMiddleware(MiddlewareMixin):
    """Redirect unauthenticated users to login page."""
    
    # URLs that don't require authentication
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/webdev/',  # Development template viewer
        '/static/',  # Static files
    ]
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check if user is authenticated, redirect to login if not."""
        
        # Skip authentication check for exempt URLs
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return None
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            client_ip = self._get_client_ip(request)
            
            logger.info(
                f"Unauthenticated access to {request.path}, redirecting to login",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'ip': client_ip,
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                }
            )
            
            # Build login URL with next parameter
            from django.urls import reverse
            
            login_url = reverse('accounts:login')
            if request.path != '/':
                login_url += f'?next={request.path}'
            
            return HttpResponseRedirect(login_url)
        
        return None
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or 'Unknown'
