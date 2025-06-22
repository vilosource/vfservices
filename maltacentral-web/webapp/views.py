import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from .logging_utils import log_view_access, webapp_logger, get_client_ip

# Get logger for this module
logger = logging.getLogger(__name__)

@log_view_access('home_page')
def home(request: HttpRequest) -> HttpResponse:
    """Render the demo home page."""
    logger.debug(
        "Home page view started",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
    )
    
    try:
        webapp_logger.info(
            "Home page accessed",
            user=str(request.user) if request.user.is_authenticated else 'Anonymous',
            ip=get_client_ip(request),
            session_key=request.session.session_key or "No session",
        )
        
        logger.info("Rendering home page template")
        response = render(request, "webapp/index.html")
        
        logger.debug(
            "Home page rendered successfully",
            extra={
                'status_code': 200,
                'template': 'webapp/index.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        webapp_logger.error(f"Failed to render home page: {str(e)}", exc_info=True)
        logger.error(
            f"Home page rendering failed: {str(e)}",
            extra={
                'template': 'webapp/index.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@login_required
@log_view_access('private_page')
def private(request: HttpRequest) -> HttpResponse:
    """Simplified request inspector for JWT middleware analysis."""
    
    logger.debug(
        "Private page view started - JWT user authenticated",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'method': request.method,
            'path': request.path,
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'auth_backend': getattr(request.user, 'backend', 'Unknown'),
        }
    )   

    try:
        access_time = timezone.now()
        
        logger.info(
            f"Private page accessed by JWT user: {getattr(request.user, 'username', 'Unknown')}",
            extra={
                'user_id': getattr(request.user, 'id', 'No ID (JWT User)'),
                'username': getattr(request.user, 'username', 'Unknown'),
                'email': getattr(request.user, 'email', 'Unknown'),
                'is_staff': getattr(request.user, 'is_staff', False),
                'is_superuser': getattr(request.user, 'is_superuser', False),
                'backend': getattr(request.user, 'backend', 'Unknown'),
                'access_time': access_time.isoformat(),
            }
        )
        
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
        client_ip = get_client_ip(request)
        
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
        logger.error(
            f"Private page rendering failed: {str(e)}",
            extra={
                'template': 'webapp/private.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise


@log_view_access('dashboard_page')
def dashboard(request: HttpRequest) -> HttpResponse:
    """Render the dashboard page with dynamic menu."""
    logger.debug(
        "Dashboard page view started",
        extra={
            'user': str(request.user),
            'ip': get_client_ip(request),
            'method': request.method,
            'path': request.path,
        }
    )
    
    try:
        webapp_logger.info(
            "Dashboard page accessed",
            user=str(request.user),
            ip=get_client_ip(request),
        )
        
        context = {
            'user': request.user,
            'user_attrs': getattr(request, 'user_attrs', None),
        }
        
        logger.info("Rendering dashboard page template")
        response = render(request, "webapp/dashboard.html", context)
        
        logger.debug(
            "Dashboard page rendered successfully",
            extra={
                'status_code': 200,
                'template': 'webapp/dashboard.html',
                'user': str(request.user),
            }
        )
        
        return response
        
    except Exception as e:
        webapp_logger.error(f"Failed to render dashboard page: {str(e)}", exc_info=True)
        logger.error(
            f"Dashboard page rendering failed: {str(e)}",
            extra={
                'template': 'webapp/dashboard.html',
                'error_type': type(e).__name__,
                'user': str(request.user),
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise