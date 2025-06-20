import logging
from django.shortcuts import render
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.conf import settings
from webapp.logging_utils import log_view_access, get_client_ip
from .identity_client import IdentityProviderClient

# Get logger for this module
logger = logging.getLogger(__name__)

@log_view_access('login_page')
@csrf_protect
@never_cache
def login_view(request: HttpRequest) -> HttpResponse:
    """Handle both GET (render form) and POST (authenticate) requests."""
    
    if request.method == "GET":
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
            # Check if user is already authenticated
            if request.user.is_authenticated:
                logger.info(
                    f"Already authenticated user {request.user} accessed login page",
                    extra={
                        'user': str(request.user),
                        'ip': get_client_ip(request),
                    }
                )
                return HttpResponseRedirect('/')
            
            logger.info("Rendering login template")
            response = render(request, 'accounts/login.html')
            
            logger.debug(
                "Login template rendered successfully",
                extra={
                    'status_code': 200,
                    'template': 'accounts/login.html',
                    'user': 'Anonymous',
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Failed to render login page: {str(e)}",
                extra={
                    'template': 'accounts/login.html',
                    'error_type': type(e).__name__,
                    'user': 'Anonymous',
                    'ip': get_client_ip(request),
                },
                exc_info=True
            )
            raise
        
    elif request.method == "POST":
        username = request.POST.get("email")  # Form uses email field
        password = request.POST.get("password")
        remember_me = request.POST.get("remember")
        
        logger.info(
            f"Login attempt for user: {username}",
            extra={
                'username': username,
                'ip': get_client_ip(request),
                'remember_me': bool(remember_me),
            }
        )
        
        if not username or not password:
            logger.warning(
                "Login attempt with missing credentials",
                extra={
                    'username': username or 'Missing',
                    'password_provided': bool(password),
                    'ip': get_client_ip(request),
                }
            )
            messages.error(request, "Email and password are required")
            return render(request, 'accounts/login.html')
        
        # Authenticate via identity provider
        client = IdentityProviderClient()
        result = client.authenticate_user(username, password, request)
        
        if "error" in result:
            logger.warning(
                f"Authentication failed for user: {username} - {result['error']}",
                extra={
                    'username': username,
                    'ip': get_client_ip(request),
                    'error': result['error'],
                }
            )
            messages.error(request, result["error"])
            return render(request, 'accounts/login.html')
        
        # Authentication successful - set JWT cookie and redirect
        redirect_url = request.GET.get('next', '/')
        
        logger.info(
            f"Login successful for user: {username}, redirecting to: {redirect_url}",
            extra={
                'username': username,
                'ip': get_client_ip(request),
                'redirect_url': redirect_url,
            }
        )
        
        response = HttpResponseRedirect(redirect_url)
        
        # Set JWT cookie with appropriate settings
        cookie_max_age = 86400 if remember_me else 3600  # 24 hours or 1 hour
        response.set_cookie(
            'jwt',
            result['token'],
            domain=settings.SSO_COOKIE_DOMAIN,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=cookie_max_age
        )
        
        # Set a separate cookie for JavaScript access (for API calls)
        response.set_cookie(
            'jwt_token',
            result['token'],
            domain=settings.SSO_COOKIE_DOMAIN,
            httponly=False,  # JavaScript accessible
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=cookie_max_age
        )
        
        messages.success(request, "Login successful")
        return response

@log_view_access('logout_page')
@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    """Handle logout - clear JWT cookie."""
    
    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        
        logger.info(
            f"Logout initiated for user: {user}",
            extra={
                'user': str(user) if user else 'Anonymous',
                'ip': get_client_ip(request),
            }
        )
        
        response = HttpResponseRedirect(reverse('accounts:login'))
        
        # Set cookies to empty value with max_age=0 to ensure deletion
        cookie_settings = {
            'value': '',
            'domain': settings.SSO_COOKIE_DOMAIN,
            'path': '/',
            'max_age': 0,
            'expires': 'Thu, 01 Jan 1970 00:00:00 GMT',
            'secure': not settings.DEBUG,
            'httponly': True,
            'samesite': 'Lax'
        }
        
        # Clear jwt cookie (httponly)
        response.set_cookie('jwt', **cookie_settings)
        
        # Clear jwt_token cookie (not httponly for JavaScript access)
        cookie_settings['httponly'] = False
        response.set_cookie('jwt_token', **cookie_settings)
        
        # Also delete using delete_cookie as a fallback
        response.delete_cookie('jwt', domain=settings.SSO_COOKIE_DOMAIN, path='/')
        response.delete_cookie('jwt_token', domain=settings.SSO_COOKIE_DOMAIN, path='/')
        
        logger.debug(
            f"Cleared JWT cookies for domain: {settings.SSO_COOKIE_DOMAIN}",
            extra={
                'sso_domain': settings.SSO_COOKIE_DOMAIN,
                'user': str(user) if user else 'Anonymous',
            }
        )
        
        messages.success(request, "Logged out successfully")
        
        logger.info(
            f"Logout completed for user: {user}",
            extra={
                'user': str(user) if user else 'Anonymous',
                'ip': get_client_ip(request),
            }
        )
        
        return response
    
    # GET request - render logout confirmation page
    logger.debug(
        "Logout page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    return render(request, 'accounts/logout.html')


@log_view_access('profile_page')
@login_required
def profile_view(request: HttpRequest) -> HttpResponse:
    """Render the user profile page."""
    
    logger.debug(
        "Profile page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        # Pass external service URLs to the template for JavaScript API calls
        context = {
            'identity_service_url': settings.EXTERNAL_SERVICE_URLS['identity'],
            'user': request.user,
        }
        
        logger.info(
            f"Rendering profile page for user: {request.user}",
            extra={
                'user': str(request.user),
                'ip': get_client_ip(request),
                'template': 'accounts/profile.html',
            }
        )
        
        return render(request, 'accounts/profile.html', context)
        
    except Exception as e:
        logger.error(
            f"Failed to render profile page for user {request.user}: {str(e)}",
            extra={
                'user': str(request.user),
                'ip': get_client_ip(request),
                'error_type': type(e).__name__,
            },
            exc_info=True
        )
        raise