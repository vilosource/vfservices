import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from .logging_utils import log_view_access, webapp_logger

# Get logger for this module
logger = logging.getLogger(__name__)

@log_view_access('home_page')
def home(request: HttpRequest) -> HttpResponse:
    """Render the demo home page."""
    try:
        webapp_logger.info(
            "Home page accessed",
            user=str(request.user) if request.user.is_authenticated else 'Anonymous',
        )
        return render(request, "webapp/index.html")
    except Exception as e:
        webapp_logger.error(f"Failed to render home page: {str(e)}", exc_info=True)
        raise

@login_required
@log_view_access('private_page')
def private(request: HttpRequest) -> HttpResponse:
    """Simplified request inspector for JWT middleware analysis."""
    
    logger.debug(
        "Private page accessed by JWT user",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': _get_client_ip(request),
            'method': request.method,
            'path': request.path,
        }
    )   

    try:
        access_time = timezone.now()
        
        # Safely extract user details from JWT middleware (no DB access)
        user_details = {
            'username': getattr(request.user, 'username', 'Unknown'),
            'email': getattr(request.user, 'email', 'Unknown'),
            'is_authenticated': request.user.is_authenticated,
            'is_active': getattr(request.user, 'is_active', False),
            'is_staff': getattr(request.user, 'is_staff', False),
            'is_superuser': getattr(request.user, 'is_superuser', False),
            'user_class': type(request.user).__name__,
            'backend': getattr(request.user, 'backend', 'Unknown'),
            'user_id': getattr(request.user, 'id', 'No ID (JWT User)'),
        }
        
        # Request details
        request_details = {
            'method': request.method,
            'path': request.path,
            'content_type': request.content_type,
            'session_key': request.session.session_key or "No session",
            'has_session': bool(request.session.session_key),
        }
        
        # Extract authentication-related headers
        auth_headers = {}
        for key, value in request.META.items():
            if any(term in key.lower() for term in ['auth', 'jwt', 'token', 'bearer']):
                # Truncate long values for display
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                auth_headers[key] = display_value
        
        # Extract key HTTP headers
        important_headers = [
            'HTTP_USER_AGENT', 'HTTP_HOST', 'HTTP_REFERER', 
            'HTTP_X_FORWARDED_FOR', 'HTTP_X_REAL_IP', 'REMOTE_ADDR'
        ]
        http_headers = {}
        for header in important_headers:
            if header in request.META:
                http_headers[header] = request.META[header]
        
        # Get client IP
        client_ip = _get_client_ip(request)
        
        context = {
            "access_time": access_time,
            "user_details": user_details,
            "request_details": request_details,
            "auth_headers": auth_headers,
            "http_headers": http_headers,
            "client_ip": client_ip,
        }
        
        webapp_logger.info(
            f"Private page accessed by JWT user: {user_details.get('username', 'Unknown')}"
        )
        
        return render(request, "webapp/private.html", context)
        
    except Exception as e:
        webapp_logger.error(f"Failed to render private page: {str(e)}", exc_info=True)
        raise


def _get_client_ip(request: HttpRequest) -> str:
    """Get the client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'Unknown')
