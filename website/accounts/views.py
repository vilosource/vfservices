import logging
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from webapp.logging_utils import log_view_access, get_client_ip

# Get logger for this module
logger = logging.getLogger(__name__)

@log_view_access('login_page')
def login_view(request: HttpRequest) -> HttpResponse:
    """Render the login page."""
    logger.debug(
        "Login page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        # Log if user is already authenticated
        if request.user.is_authenticated:
            logger.info(
                f"Already authenticated user {request.user} accessed login page",
                extra={
                    'user': str(request.user),
                    'ip': get_client_ip(request),
                }
            )
        
        logger.info("Rendering login template")
        response = render(request, 'accounts/login.html')
        
        logger.debug(
            "Login template rendered successfully",
            extra={
                'status_code': 200,
                'template': 'accounts/login.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to render login page: {str(e)}",
            extra={
                'template': 'accounts/login.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@log_view_access('logout_page')
def logout_view(request: HttpRequest) -> HttpResponse:
    """Render the logout page."""
    logger.debug(
        "Logout page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        # Log user context for logout
        if request.user.is_authenticated:
            logger.info(
                f"Authenticated user {request.user} accessed logout page",
                extra={
                    'user': str(request.user),
                    'ip': get_client_ip(request),
                }
            )
        else:
            logger.info(
                "Anonymous user accessed logout page",
                extra={
                    'ip': get_client_ip(request),
                }
            )
        
        logger.info("Rendering logout template")
        response = render(request, 'accounts/logout.html')
        
        logger.debug(
            "Logout template rendered successfully",
            extra={
                'status_code': 200,
                'template': 'accounts/logout.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to render logout page: {str(e)}",
            extra={
                'template': 'accounts/logout.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise