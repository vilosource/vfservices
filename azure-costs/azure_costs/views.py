"""
API views for Azure Costs service.
"""
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from azure_costs.logging_utils import (
    log_api_request,
    log_security_event,
    azure_costs_logger,
    api_logger
)

# Get module logger
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth(request):
    """Debug endpoint to check authentication state."""
    user_attrs = getattr(request, 'user_attrs', None)
    user_attrs_dict = None
    if user_attrs:
        # Convert UserAttributes object to dict
        user_attrs_dict = {
            "user_id": getattr(user_attrs, 'user_id', None),
            "username": getattr(user_attrs, 'username', None),
            "email": getattr(user_attrs, 'email', None),
            "roles": getattr(user_attrs, 'roles', []),
            "department": getattr(user_attrs, 'department', None),
        }
    
    return Response({
        "user_authenticated": request.user.is_authenticated,
        "user_id": getattr(request.user, 'id', None),
        "username": getattr(request.user, 'username', 'Anonymous'),
        "user_attrs": user_attrs_dict,
        "cookies_received": {
            "jwt": bool(request.COOKIES.get('jwt')),
            "jwt_token": bool(request.COOKIES.get('jwt_token'))
        },
        "service_name": getattr(settings, 'SERVICE_NAME', 'Not set')
    })


def debug_middleware(request):
    """Debug endpoint that bypasses DRF to check middleware directly."""
    from django.http import JsonResponse
    
    # Log everything about the request
    logger.debug(f"DEBUG MIDDLEWARE: Processing request to {request.path}")
    logger.debug(f"DEBUG MIDDLEWARE: User type: {type(request.user)}")
    logger.debug(f"DEBUG MIDDLEWARE: User: {request.user}")
    logger.debug(f"DEBUG MIDDLEWARE: User authenticated: {request.user.is_authenticated}")
    logger.debug(f"DEBUG MIDDLEWARE: Cookies: {dict(request.COOKIES)}")
    
    user_attrs = getattr(request, 'user_attrs', None)
    user_attrs_dict = None
    if user_attrs:
        user_attrs_dict = {
            "user_id": getattr(user_attrs, 'user_id', None),
            "username": getattr(user_attrs, 'username', None),
            "email": getattr(user_attrs, 'email', None),
            "roles": getattr(user_attrs, 'roles', []),
            "department": getattr(user_attrs, 'department', None),
        }
    
    response_data = {
        "middleware_check": "Direct Django view (no DRF)",
        "user_type": str(type(request.user)),
        "user_authenticated": request.user.is_authenticated,
        "user_id": getattr(request.user, 'id', None),
        "username": getattr(request.user, 'username', 'Anonymous'),
        "user_attrs": user_attrs_dict,
        "has_cached_user": hasattr(request, '_cached_user'),
        "cached_user": str(getattr(request, '_cached_user', None)) if hasattr(request, '_cached_user') else None,
        "cookies_received": {
            "jwt": bool(request.COOKIES.get('jwt')),
            "jwt_token": bool(request.COOKIES.get('jwt_token')),
            "all_cookies": list(request.COOKIES.keys())
        },
        "middleware_order": [
            "JWTAuthenticationMiddleware runs BEFORE AuthenticationMiddleware",
            "So request.user should be set by JWT middleware"
        ]
    }
    
    return JsonResponse(response_data)

@swagger_auto_schema(
    method='get',
    operation_description="Health check endpoint - public access. Returns service status and basic information.",
    responses={
        200: openapi.Response(
            description="Service is healthy",
            examples={
                "application/json": {
                    "status": "healthy",
                    "service": "azure-costs-api",
                    "version": "1.0.0",
                    "timestamp": "2025-06-20T10:30:00Z"
                }
            }
        )
    },
    tags=['Health']
)
@api_view(['GET'])
@permission_classes([AllowAny])
@log_api_request('health_check')
def health(request):
    """
    Health check endpoint - public access.
    Returns service status and basic information.
    """
    logger.debug("Health check requested", extra={
        'ip': request.META.get('REMOTE_ADDR', 'Unknown'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown')
    })
    
    response_data = {
        "status": "healthy",
        "service": "azure-costs-api",
        "version": "1.0.0",
        "timestamp": timezone.now().isoformat()
    }
    
    logger.info("Health check successful", extra={
        'response': response_data
    })
    
    return Response(response_data, status=status.HTTP_200_OK)


@swagger_auto_schema(
    method='get',
    operation_description="Private endpoint - requires JWT authentication and Azure Costs API access. Returns user information and authentication details.",
    security=[{'JWT': []}],
    responses={
        200: openapi.Response(
            description="User authenticated and authorized",
            examples={
                "application/json": {
                    "message": "Azure Costs API - Private Endpoint",
                    "service": "azure_costs",
                    "user": {
                        "id": 8,
                        "username": "alice",
                        "email": "alice@example.com"
                    },
                    "roles": ["costs_manager", "costs_admin"],
                    "permissions": {
                        "can_view_all_costs": True,
                        "can_export_reports": False,
                        "can_modify_tags": False,
                        "assigned_subscriptions": [],
                        "assigned_cost_centers": []
                    },
                    "timestamp": "2025-06-20T10:30:00Z"
                }
            }
        ),
        401: openapi.Response(description="Authentication required"),
        403: openapi.Response(description="User lacks Azure Costs roles")
    },
    tags=['Private']
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_request('private_endpoint')
def private(request):
    """
    Private endpoint - requires JWT authentication and Azure Costs API access.
    Returns user information and authentication details.
    """
    user = request.user
    
    user_attrs = getattr(request, 'user_attrs', None)
    
    # Check if user has any Azure Costs role
    if user_attrs:
        roles = getattr(user_attrs, 'roles', [])
    else:
        roles = []
    
    allowed_roles = ['costs_admin', 'costs_manager', 'costs_analyst', 'costs_viewer']
    has_access = any(role in roles for role in allowed_roles)
    
    if not has_access:
        logger.warning(f"User {user.username} lacks Azure Costs roles", extra={
            'user_id': user.id,
            'username': user.username,
            'roles': roles
        })
        return Response(
            {"detail": "You don't have permission to access Azure Costs API"},
            status=status.HTTP_403_FORBIDDEN
        )
    
    logger.info(f"Private endpoint accessed by user {user.id}", extra={
        'user_id': user.id,
        'username': user.username,
        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
    })
    
    response_data = {
        "message": "Azure Costs API - Private Endpoint",
        "service": "azure_costs",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": getattr(user, 'email', None)
        },
        "roles": getattr(user_attrs, 'roles', []) if user_attrs else [],
        "permissions": {
            "can_view_all_costs": 'costs_admin' in (getattr(user_attrs, 'roles', []) if user_attrs else []),
            "can_export_reports": getattr(user_attrs, 'can_export_reports', False) if user_attrs else False,
            "can_modify_tags": getattr(user_attrs, 'can_modify_tags', False) if user_attrs else False,
            "assigned_subscriptions": getattr(user_attrs, 'azure_subscription_ids', []) if user_attrs else [],
            "assigned_cost_centers": getattr(user_attrs, 'cost_center_ids', []) if user_attrs else []
        },
        "timestamp": timezone.now().isoformat()
    }
    
    # Log user data access
    azure_costs_logger.info("Private endpoint accessed", {
        'user_id': user.id,
        'username': user.username,
        'endpoint': 'private',
        'roles': getattr(user_attrs, 'roles', []) if user_attrs else [],
        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
    })
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@log_api_request('test_rbac')
def test_rbac(request):
    """
    RBAC test endpoint - requires JWT authentication.
    Tests RBAC/ABAC permissions by checking user roles and attributes from JWT.
    """
    user = request.user
    
    logger.debug(f"RBAC test requested by user {user.id}", extra={
        'user_id': user.id,
        'username': user.username,
        'ip': request.META.get('REMOTE_ADDR', 'Unknown')
    })
    
    # Get roles and attributes from request (set by JWT middleware)
    roles = getattr(request, 'user_roles', [])
    attributes = getattr(request, 'user_attributes', {})
    
    # Check if user has required access (example logic)
    # In real implementation, this would check against specific RBAC policies
    has_access = bool(roles) or bool(attributes)
    
    response_data = {
        "message": "RBAC test successful",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": getattr(user, 'email', None),
            "roles": roles,
            "attributes": attributes
        },
        "has_access": has_access,
        "timestamp": timezone.now().isoformat()
    }
    
    # Log RBAC check
    log_security_event(
        request=request,
        event_type='rbac_check',
        severity='info',
        details={
            'user_id': user.id,
            'roles': roles,
            'attributes': attributes,
            'has_access': has_access,
            'endpoint': 'test_rbac'
        }
    )
    
    logger.info(f"RBAC test completed for user {user.id}", extra={
        'user_id': user.id,
        'has_access': has_access,
        'roles_count': len(roles),
        'attributes_count': len(attributes)
    })
    
    return Response(response_data, status=status.HTTP_200_OK)