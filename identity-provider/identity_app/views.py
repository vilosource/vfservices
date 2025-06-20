import datetime
import logging
import sys
import os
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# Add the parent directory to Python path to access common module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.jwt_auth import utils
from .services import ManifestService
from .logging_utils import (
    log_view_access, 
    log_authentication_attempt, 
    log_jwt_operation, 
    log_login_event, 
    log_logout_event,
    log_security_event,
    get_client_ip,
    identity_logger,
    auth_logger
)

# Get logger for this module
logger = logging.getLogger(__name__)
auth_logger = logging.getLogger('identity_app.authentication')
jwt_logger = logging.getLogger('identity_app.jwt')
security_logger = logging.getLogger('identity_app.security')
identity_logger = logging.getLogger('identity_app')


def get_application_domain(request: HttpRequest) -> str:
    """
    Determine which application domain is accessing the identity service.
    
    Args:
        request: The HTTP request object
        
    Returns:
        The application domain (e.g., 'vfservices.viloforge.com' or 'cielo.viloforge.com')
    """
    host = request.get_host()
    
    # Remove port if present
    if ':' in host:
        host = host.split(':')[0]
    
    # If accessed via identity.<domain>, extract the domain
    if host.startswith('identity.'):
        return host[9:]  # Remove 'identity.' prefix
    
    # Default to the first allowed domain
    allowed_domains = getattr(settings, 'ALLOWED_APPLICATION_DOMAINS', ['vfservices.viloforge.com'])
    return allowed_domains[0]


def validate_redirect_url(url: str) -> bool:
    """
    Validate that a redirect URL is allowed based on configured domains.
    
    Args:
        url: The redirect URL to validate
        
    Returns:
        True if the URL is allowed, False otherwise
    """
    if not url:
        return True  # Empty URL is allowed, will use default
        
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        
        # Ensure the URL has a valid scheme (https or http)
        if parsed_url.scheme not in ['http', 'https']:
            logger.warning(
                f"Redirect URL validation failed: invalid scheme {parsed_url.scheme}",
                extra={'url': url, 'scheme': parsed_url.scheme}
            )
            return False
        
        # Extract the hostname from the URL
        hostname = parsed_url.netloc
        if not hostname:
            return False
            
        # Remove port if present
        if ':' in hostname:
            hostname = hostname.split(':')[0]
            
        # Check against allowed domains
        allowed_domains = getattr(settings, 'ALLOWED_REDIRECT_DOMAINS', [])
        
        # Check exact match or subdomain match
        for allowed_domain in allowed_domains:
            if hostname == allowed_domain:
                return True
            # Check if it's a subdomain of an allowed domain
            if hostname.endswith(f'.{allowed_domain}'):
                return True
                
        logger.warning(
            f"Redirect URL validation failed: {url} (hostname: {hostname}) not in allowed domains",
            extra={
                'url': url,
                'hostname': hostname,
                'allowed_domains': allowed_domains
            }
        )
        return False
        
    except Exception as e:
        logger.error(
            f"Error validating redirect URL: {str(e)}",
            extra={
                'url': url,
                'error_type': type(e).__name__
            }
        )
        return False


@log_view_access('index_page')
def index(request: HttpRequest) -> HttpResponse:
    """Render the index page with a welcome message."""
    logger.debug(
        "Identity provider index page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        logger.info("Rendering identity provider index page")
        
        context = {
            "message": "Welcome to the Identity Provider!",
            "service": "identity-provider",
            "version": "1.0.0",
            "timestamp": timezone.now().isoformat(),
        }
        
        identity_logger.info(
            "Index page rendered successfully",
            extra={
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'client_ip': get_client_ip(request)
            }
        )
        
        return render(request, "identity_app/index.html", context)
        
    except Exception as e:
        logger.error(
            f"Failed to render identity provider index: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

def index_view(request: HttpRequest) -> HttpResponse:
    """
    Root URL handler - redirects to login page
    """
    return HttpResponseRedirect('/login/')

@log_view_access('login_page')
def login_user(request: HttpRequest) -> HttpResponse:
    """Render login form or authenticate user and set JWT cookie."""
    redirect_uri = request.GET.get('redirect_uri') or request.POST.get('redirect_uri')
    logger.debug(
        "Login page accessed",
        extra={
            'method': request.method,
            'redirect_uri': redirect_uri,
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        if request.method == "GET":
            logger.info("Rendering login form")
            
            # Check if user is already authenticated
            if request.user.is_authenticated:
                logger.info(
                    f"Already authenticated user {request.user} accessed login page",
                    extra={
                        'user': str(request.user),
                        'ip': get_client_ip(request),
                        'redirect_uri': redirect_uri,
                    }
                )
                
                log_security_event(
                    'authenticated_user_accessed_login',
                    request=request,
                    user=request.user,
                    severity='INFO',
                    details={'redirect_uri': redirect_uri}
                )
            
            return render(request, "identity_app/login.html")

        # Handle POST request - authentication
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        logger.info(
            f"Authentication attempt for username: {username}",
            extra={
                'username': username,
                'ip': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'redirect_uri': redirect_uri,
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
            
            log_authentication_attempt(
                request, 
                username or 'Unknown', 
                False, 
                'Missing username or password'
            )
            
            return HttpResponseForbidden("Username and password are required")
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            logger.warning(
                f"Authentication failed for username: {username}",
                extra={
                    'username': username,
                    'ip': get_client_ip(request),
                    'failure_reason': 'Invalid credentials',
                }
            )
            
            log_authentication_attempt(request, username, False, 'Invalid credentials')
            log_login_event(request, username, False, redirect_uri)
            
            return HttpResponseForbidden("Invalid login")

        # Authentication successful
        logger.info(
            f"Authentication successful for user: {username}",
            extra={
                'username': username,
                'user_id': user.id,
                'user_email': user.email,
                'is_staff': user.is_staff,
                'ip': get_client_ip(request),
            }
        )
        
        log_authentication_attempt(request, username, True, user=user)

        # Create JWT token
        payload = {
            "user_id": user.id,  # Add user_id for RBAC lookups
            "username": user.username,
            "email": user.email,
            "iat": datetime.datetime.utcnow(),
        }
        
        try:
            token = utils.encode_jwt(payload)
            
            log_jwt_operation(
                'token_created',
                username=user.username,
                token_data=payload,
                request=request,
                success=True
            )
            
            logger.info(
                f"JWT token created for user: {username}",
                extra={
                    'username': username,
                    'user_id': user.id,
                    'token_payload': payload,
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to create JWT token for user {username}: {str(e)}",
                extra={
                    'username': username,
                    'user_id': user.id,
                    'error_type': type(e).__name__,
                },
                exc_info=True
            )
            
            log_jwt_operation(
                'token_creation_failed',
                username=user.username,
                request=request,
                success=False,
                error=str(e)
            )
            
            return HttpResponseForbidden("Authentication system error")

        # Set up redirect - check GET parameters (from URL) since form preserves full path
        # Use dynamic domain detection for default redirect
        application_domain = get_application_domain(request)
        default_redirect = f"https://{application_domain}"
        redirect_url = request.GET.get("redirect_uri", default_redirect)
        
        # Validate redirect URL for security
        if not validate_redirect_url(redirect_url):
            log_security_event(
                'invalid_redirect_url',
                request=request,
                user=user,
                severity='WARNING',
                details={'redirect_url': redirect_url, 'username': username}
            )
            redirect_url = default_redirect
            logger.warning(
                f"Invalid redirect URL attempted for user {username}, using default",
                extra={
                    'username': username,
                    'user_id': user.id,
                    'attempted_redirect': request.GET.get("redirect_uri"),
                    'default_redirect': redirect_url,
                }
            )
        
        logger.info(
            f"Redirecting authenticated user {username} to: {redirect_url}",
            extra={
                'username': username,
                'user_id': user.id,
                'redirect_url': redirect_url,
                'original_redirect_uri': redirect_uri,
            }
        )
        
        response = HttpResponseRedirect(redirect_url)
        response.set_cookie(
            "jwt",
            token,
            domain=settings.SSO_COOKIE_DOMAIN,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=3600,
        )
        
        log_login_event(request, username, True, redirect_url, user)
        
        auth_logger.info(
            "User login completed successfully",
            extra={
                'username': username,
                'user_id': user.id,
                'redirect_url': redirect_url,
                'client_ip': get_client_ip(request)
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Login process failed: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'method': request.method,
                'redirect_uri': redirect_uri,
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@log_view_access('logout_page')
def logout_user(request: HttpRequest) -> HttpResponse:
    """Clear the JWT cookie across the domain."""
    logger.debug(
        "Logout initiated",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        user = request.user if request.user.is_authenticated else None
        
        if user:
            logger.info(
                f"User logout: {user.username}",
                extra={
                    'username': user.username,
                    'user_id': user.id,
                    'ip': get_client_ip(request),
                }
            )
        else:
            logger.info(
                "Anonymous user logout (clearing cookie)",
                extra={
                    'ip': get_client_ip(request),
                }
            )
        
        log_logout_event(request, user)
        
        response = HttpResponseRedirect(settings.DEFAULT_REDIRECT_URL)
        response.delete_cookie("jwt", domain=settings.SSO_COOKIE_DOMAIN)
        
        logger.info(
            f"Logout completed, redirecting to: {settings.DEFAULT_REDIRECT_URL}",
            extra={
                'user': str(user) if user else 'Anonymous',
                'redirect_url': settings.DEFAULT_REDIRECT_URL,
            }
        )
        
        auth_logger.info(
            "User logout completed",
            extra={
                'user': str(user) if user else 'Anonymous',
                'redirect_url': settings.DEFAULT_REDIRECT_URL,
                'client_ip': get_client_ip(request)
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Logout process failed: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise
    

class LoginAPIView(APIView):
    """API endpoint to obtain JWT via username and password."""

    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Authenticate user and obtain JWT token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            },
            example={
                'username': 'user@example.com',
                'password': 'password123'
            }
        ),
        responses={
            200: openapi.Response(
                description='Authentication successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT token')
                    }
                )
            ),
            400: 'Bad Request - Missing username or password',
            401: 'Unauthorized - Invalid credentials',
            500: 'Internal Server Error'
        },
        tags=['Authentication']
    )
    def post(self, request):
        """Handle API login requests."""
        logger.debug(
            "API login endpoint accessed",
            extra={
                'ip': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        try:
            # Access request.data to trigger parsing
            try:
                data = request.data
                username = data.get("username")
                password = data.get("password")
            except Exception as parse_error:
                logger.warning(
                    f"API login request with invalid data format: {str(parse_error)}",
                    extra={
                        'ip': get_client_ip(request),
                        'error_type': type(parse_error).__name__,
                    }
                )
                return Response(
                    {"detail": "Invalid request format"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.info(
                f"API authentication attempt for username: {username}",
                extra={
                    'username': username,
                    'ip': get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
                }
            )
            
            if not username or not password:
                logger.warning(
                    "API login attempt with missing credentials",
                    extra={
                        'username': username or 'Missing',
                        'password_provided': bool(password),
                        'ip': get_client_ip(request),
                    }
                )
                
                log_authentication_attempt(
                    request, 
                    username or 'Unknown', 
                    False, 
                    'Missing username or password (API)'
                )
                
                return Response(
                    {"detail": "Username and password are required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = authenticate(username=username, password=password)
            
            if user is None:
                logger.warning(
                    f"API authentication failed for username: {username}",
                    extra={
                        'username': username,
                        'ip': get_client_ip(request),
                        'failure_reason': 'Invalid credentials',
                    }
                )
                
                log_authentication_attempt(request, username, False, 'Invalid credentials (API)')
                
                return Response(
                    {"detail": "Invalid credentials"}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Authentication successful
            logger.info(
                f"API authentication successful for user: {username}",
                extra={
                    'username': username,
                    'user_email': user.email,
                    'is_staff': user.is_staff,
                    'ip': get_client_ip(request),
                }
            )
            
            log_authentication_attempt(request, username, True, user=user)

            # Create JWT token
            payload = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "iat": timezone.now(),
            }
            
            try:
                token = utils.encode_jwt(payload)
                
                log_jwt_operation(
                    'api_token_created',
                    username=user.username,
                    token_data=payload,
                    request=request,
                    success=True
                )
                
                logger.info(
                    f"JWT token created via API for user: {username}",
                    extra={
                        'username': username,
                        'token_payload': payload,
                    }
                )
                
                auth_logger.info(
                    "API login completed successfully",
                    extra={
                        'username': username,
                        'client_ip': get_client_ip(request),
                        'endpoint': 'api'
                    }
                )
                
                return Response({"token": token})
                
            except Exception as e:
                logger.error(
                    f"Failed to create JWT token via API for user {username}: {str(e)}",
                    extra={
                        'username': username,
                        'error_type': type(e).__name__,
                    },
                    exc_info=True
                )
                
                log_jwt_operation(
                    'api_token_creation_failed',
                    username=user.username,
                    request=request,
                    success=False,
                    error=str(e)
                )
                
                return Response(
                    {"detail": "Authentication system error"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        except Exception as e:
            logger.error(
                f"API login process failed: {str(e)}",
                extra={
                    'error_type': type(e).__name__,
                    'ip': get_client_ip(request),
                },
                exc_info=True
            )
            
            return Response(
                {"detail": "Internal server error"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class APIInfoView(APIView):
    """API endpoint that provides information about available API endpoints."""
    
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Get information about available API endpoints",
        responses={
            200: openapi.Response(
                description='API information',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'service': openapi.Schema(type=openapi.TYPE_STRING, description='Service name'),
                        'version': openapi.Schema(type=openapi.TYPE_STRING, description='API version'),
                        'endpoints': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description='Available API endpoints'
                        ),
                        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='Response timestamp')
                    }
                )
            )
        },
        tags=['API Info']
    )
    def get(self, request):
        """Return API information and available endpoints."""
        logger.info(
            "API info endpoint accessed",
            extra={
                'ip': get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            }
        )
        
        api_info = {
            "service": "Identity Provider API",
            "version": "1.0.0",
            "description": "Authentication and JWT token management service",
            "endpoints": {
                "/api/": {
                    "method": "GET",
                    "description": "Get API information",
                    "authentication": "None"
                },
                "/api/login/": {
                    "method": "POST", 
                    "description": "Authenticate user and obtain JWT token",
                    "authentication": "None",
                    "parameters": {
                        "username": "string (required)",
                        "password": "string (required)"
                    },
                    "returns": {
                        "token": "JWT token string"
                    }
                },
                "/api/status/": {
                    "method": "GET",
                    "description": "API health check and status",
                    "authentication": "None"
                },
                "/api/profile/": {
                    "method": "GET",
                    "description": "Get user profile information",
                    "authentication": "JWT Token Required",
                    "returns": {
                        "username": "string",
                        "email": "string",
                        "timestamp": "ISO datetime"
                    }
                },
                "/api/docs/": {
                    "method": "GET",
                    "description": "Interactive API documentation (Swagger UI)",
                    "authentication": "None"
                },
                "/api/redoc/": {
                    "method": "GET", 
                    "description": "Alternative API documentation (ReDoc)",
                    "authentication": "None"
                },
                "/api/services/register/": {
                    "method": "POST",
                    "description": "Register or update a service RBAC/ABAC manifest",
                    "authentication": "Service Token (future)",
                    "parameters": {
                        "service": "string (required) - Service identifier",
                        "display_name": "string (required) - Human-readable name",
                        "roles": "array (required) - Service roles",
                        "attributes": "array (required) - Service attributes"
                    },
                    "returns": {
                        "service": "string",
                        "version": "integer - Manifest version",
                        "status": "string",
                        "roles_created": "integer",
                        "attributes_created": "integer"
                    }
                }
            },
            "authentication": {
                "type": "JWT Token",
                "description": "Use the token obtained from /api/login/ in the Authorization header",
                "header_format": "Authorization: Bearer <token>"
            },
            "timestamp": timezone.now().isoformat()
        }
        
        return Response(api_info)


@api_view(['GET'])
@permission_classes([AllowAny])
@swagger_auto_schema(
    operation_description="Get API status and health check",
    responses={
        200: openapi.Response(
            description='API status',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'status': openapi.Schema(type=openapi.TYPE_STRING, description='API status'),
                    'service': openapi.Schema(type=openapi.TYPE_STRING, description='Service name'),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='Response timestamp')
                }
            )
        )
    },
    tags=['API Info']
)
def api_status(request):
    """API health check endpoint."""
    logger.debug(
        "API status endpoint accessed",
        extra={
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
    )
    
    return Response({
        "status": "healthy",
        "service": "identity-provider",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@swagger_auto_schema(
    operation_description="Get user profile information",
    responses={
        200: openapi.Response(
            description='User profile information',
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                    'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address'),
                    'timestamp': openapi.Schema(type=openapi.TYPE_STRING, description='Response timestamp')
                }
            )
        ),
        401: 'Unauthorized - Valid JWT token required'
    },
    tags=['User Profile']
)
def api_profile(request):
    """API endpoint to get user profile information."""
    logger.debug(
        "API profile endpoint accessed",
        extra={
            'user': str(request.user),
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
    )
    
    try:
        # Get the Django user object
        from django.contrib.auth.models import User
        from .models import UserRole
        
        user = None
        if hasattr(request.user, 'id'):
            try:
                user = User.objects.get(id=request.user.id)
            except User.DoesNotExist:
                pass
        
        if not user:
            return Response(
                {"detail": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user's active roles
        active_roles = UserRole.objects.filter(
            user=user
        ).select_related('role__service').order_by('-granted_at')
        
        roles_data = []
        for user_role in active_roles:
            if user_role.is_active:
                roles_data.append({
                    "role_name": user_role.role.name,
                    "service_name": user_role.role.service.name,
                    "is_active": True
                })
        
        user_profile = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": roles_data,
            "timestamp": timezone.now().isoformat()
        }
        
        logger.info(
            f"Profile retrieved for user: {user.username}",
            extra={
                'username': user.username,
                'user_id': user.id,
                'role_count': len(roles_data),
                'ip': get_client_ip(request),
            }
        )
        
        identity_logger.info(
            "User profile retrieved successfully",
            extra={
                'user': user.username,
                'client_ip': get_client_ip(request)
            }
        )
        
        return Response(user_profile)
        
    except Exception as e:
        logger.error(
            f"Failed to retrieve profile for user {request.user.username}: {str(e)}",
            extra={
                'username': request.user.username,
                'error_type': type(e).__name__,
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        
        return Response(
            {"detail": "Failed to retrieve profile"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@method_decorator(csrf_exempt, name='dispatch')
class ServiceRegisterView(APIView):
    """API endpoint for services to register their RBAC manifests."""
    
    authentication_classes = []  # Service-to-service auth would go here
    permission_classes = [AllowAny]  # In production, use service auth
    
    @swagger_auto_schema(
        operation_description="Register or update a service manifest for RBAC/ABAC",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['service', 'display_name', 'manifest_version', 'roles', 'attributes'],
            properties={
                'service': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='Service identifier (e.g., billing_api)',
                    pattern='^[a-z][a-z0-9_-]*$'
                ),
                'display_name': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Human-readable service name'
                ),
                'description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Service description'
                ),
                'manifest_version': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Version of the manifest schema',
                    default='1.0'
                ),
                'roles': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['name', 'display_name'],
                        properties={
                            'name': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Role identifier',
                                pattern='^[a-z][a-z0-9_]*$'
                            ),
                            'display_name': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Human-readable role name'
                            ),
                            'description': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='What this role allows'
                            ),
                            'is_global': openapi.Schema(
                                type=openapi.TYPE_BOOLEAN,
                                description='If true, role applies to entire service',
                                default=True
                            )
                        }
                    )
                ),
                'attributes': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        required=['name', 'display_name', 'type'],
                        properties={
                            'name': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Attribute identifier',
                                pattern='^[a-z][a-z0-9_]*$'
                            ),
                            'display_name': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Human-readable attribute name'
                            ),
                            'description': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='What this attribute represents'
                            ),
                            'type': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Data type',
                                enum=['string', 'integer', 'boolean', 'list_string', 'list_integer', 'json']
                            ),
                            'is_required': openapi.Schema(
                                type=openapi.TYPE_BOOLEAN,
                                description='Whether all users must have this attribute',
                                default=False
                            ),
                            'default_value': openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description='Default value (JSON encoded)'
                            )
                        }
                    )
                )
            },
            example={
                "service": "billing_api",
                "display_name": "Billing API Service",
                "description": "Handles invoicing and payment processing",
                "manifest_version": "1.0",
                "roles": [
                    {
                        "name": "billing_admin",
                        "display_name": "Billing Administrator",
                        "description": "Full access to all billing operations",
                        "is_global": True
                    },
                    {
                        "name": "invoice_viewer",
                        "display_name": "Invoice Viewer",
                        "description": "Can view invoices but not modify",
                        "is_global": False
                    }
                ],
                "attributes": [
                    {
                        "name": "department",
                        "display_name": "Department",
                        "description": "User's department for access control",
                        "type": "string",
                        "is_required": False
                    },
                    {
                        "name": "customer_ids",
                        "display_name": "Accessible Customer IDs",
                        "description": "List of customer IDs user can access",
                        "type": "list_integer",
                        "is_required": False,
                        "default_value": "[]"
                    }
                ]
            }
        ),
        responses={
            200: openapi.Response(
                description='Service manifest registered successfully',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'service': openapi.Schema(type=openapi.TYPE_STRING),
                        'version': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'status': openapi.Schema(type=openapi.TYPE_STRING),
                        'roles_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'roles_updated': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'attributes_created': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'attributes_updated': openapi.Schema(type=openapi.TYPE_INTEGER)
                    }
                )
            ),
            400: 'Bad Request - Invalid manifest data',
            500: 'Internal Server Error'
        },
        tags=['Service Management']
    )
    def post(self, request):
        """Register or update a service manifest."""
        logger.info(
            "Service manifest registration request received",
            extra={
                'ip': get_client_ip(request),
                'data': request.data
            }
        )
        
        try:
            # Validate required fields
            required_fields = ['service', 'display_name', 'roles', 'attributes']
            missing_fields = [f for f in required_fields if f not in request.data]
            
            if missing_fields:
                return Response(
                    {
                        "detail": f"Missing required fields: {', '.join(missing_fields)}",
                        "missing_fields": missing_fields
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract manifest data
            manifest_data = {
                'service': request.data['service'],
                'display_name': request.data['display_name'],
                'description': request.data.get('description', ''),
                'manifest_version': request.data.get('manifest_version', '1.0'),
                'roles': request.data['roles'],
                'attributes': request.data['attributes']
            }
            
            # Validate service name format
            import re
            if not re.match(r'^[a-z][a-z0-9_-]*$', manifest_data['service']):
                return Response(
                    {
                        "detail": "Invalid service name format. Must start with lowercase letter and contain only lowercase letters, numbers, hyphens, and underscores."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate roles
            for role in manifest_data['roles']:
                if 'name' not in role or 'display_name' not in role:
                    return Response(
                        {
                            "detail": "Each role must have 'name' and 'display_name' fields"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not re.match(r'^[a-z][a-z0-9_]*$', role['name']):
                    return Response(
                        {
                            "detail": f"Invalid role name format: {role['name']}. Must start with lowercase letter and contain only lowercase letters, numbers, and underscores."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Validate attributes
            valid_types = ['string', 'integer', 'boolean', 'list_string', 'list_integer', 'json']
            for attr in manifest_data['attributes']:
                if 'name' not in attr or 'display_name' not in attr or 'type' not in attr:
                    return Response(
                        {
                            "detail": "Each attribute must have 'name', 'display_name', and 'type' fields"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if not re.match(r'^[a-z][a-z0-9_]*$', attr['name']):
                    return Response(
                        {
                            "detail": f"Invalid attribute name format: {attr['name']}. Must start with lowercase letter and contain only lowercase letters, numbers, and underscores."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                if attr['type'] not in valid_types:
                    return Response(
                        {
                            "detail": f"Invalid attribute type: {attr['type']}. Must be one of: {', '.join(valid_types)}"
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Register the manifest
            manifest_service = ManifestService()
            result = manifest_service.register_manifest(
                manifest_data,
                ip_address=get_client_ip(request)
            )
            
            logger.info(
                f"Service manifest registered successfully for {manifest_data['service']}",
                extra={
                    'service': manifest_data['service'],
                    'version': result['version'],
                    'ip': get_client_ip(request)
                }
            )
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(
                f"Failed to register service manifest: {str(e)}",
                extra={
                    'error_type': type(e).__name__,
                    'ip': get_client_ip(request)
                },
                exc_info=True
            )
            
            return Response(
                {"detail": "Failed to register manifest"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshUserCacheView(APIView):
    """API endpoint to refresh user attributes in Redis cache."""
    
    authentication_classes = []  # This endpoint is called internally by services
    permission_classes = []
    
    @swagger_auto_schema(
        operation_description="Refresh user attributes in Redis cache",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['user_id', 'service_name'],
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='User ID'),
                'service_name': openapi.Schema(type=openapi.TYPE_STRING, description='Service name'),
            },
            example={
                'user_id': 1,
                'service_name': 'billing-api'
            }
        ),
        responses={
            200: 'Cache refreshed successfully',
            400: 'Bad Request - Missing user_id or service_name',
            404: 'User or service not found',
            500: 'Internal Server Error'
        },
        tags=['Cache Management']
    )
    def post(self, request):
        """Handle cache refresh requests."""
        user_id = request.data.get('user_id')
        service_name = request.data.get('service_name')
        
        if not user_id or not service_name:
            return Response(
                {"detail": "Both user_id and service_name are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Import here to avoid circular import
            from .services import RedisService
            
            # Attempt to populate user attributes
            success = RedisService.populate_user_attributes(user_id, service_name)
            
            if success:
                logger.info(
                    f"Successfully refreshed cache for user {user_id} in service {service_name}",
                    extra={
                        'user_id': user_id,
                        'service_name': service_name,
                        'ip': get_client_ip(request)
                    }
                )
                return Response(
                    {"detail": "Cache refreshed successfully"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"detail": "User or service not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(
                f"Failed to refresh cache for user {user_id}: {str(e)}",
                extra={
                    'user_id': user_id,
                    'service_name': service_name,
                    'error_type': type(e).__name__,
                    'ip': get_client_ip(request)
                },
                exc_info=True
            )
            
            return Response(
                {"detail": "Failed to refresh cache"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
