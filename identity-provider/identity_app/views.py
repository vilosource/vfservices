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
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

# Add the parent directory to Python path to access common module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.jwt_auth import utils
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
            user=str(request.user) if request.user.is_authenticated else 'Anonymous',
            client_ip=get_client_ip(request)
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

@log_view_access('login_page')
def login_user(request: HttpRequest, redirect_uri: str = None) -> HttpResponse:
    """Render login form or authenticate user and set JWT cookie."""
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

        # Set up redirect
        redirect_url = request.GET.get("redirect_uri", settings.DEFAULT_REDIRECT_URL)
        
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
            username=username,
            user_id=user.id,
            redirect_url=redirect_url,
            client_ip=get_client_ip(request)
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
            user=str(user) if user else 'Anonymous',
            redirect_url=settings.DEFAULT_REDIRECT_URL,
            client_ip=get_client_ip(request)
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
                    username=username,
                    client_ip=get_client_ip(request),
                    endpoint='api'
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
                "/api/docs/": {
                    "method": "GET",
                    "description": "Interactive API documentation (Swagger UI)",
                    "authentication": "None"
                },
                "/api/redoc/": {
                    "method": "GET", 
                    "description": "Alternative API documentation (ReDoc)",
                    "authentication": "None"
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
