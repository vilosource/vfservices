import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .logging_utils import log_api_request, billing_logger, api_logger, get_client_ip
from common.rbac_abac import RoleRequired

# Get logger for this module
logger = logging.getLogger(__name__)

@log_api_request('health_check')
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Health check endpoint for the billing API."""
    logger.debug(
        "Health check endpoint accessed",
        extra={
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        # Perform basic health checks
        health_status = {
            "status": "ok",
            "service": "billing-api",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0"
        }
        
        logger.info("Health check completed successfully")
        api_logger.info(
            "Health check endpoint response",
            status="healthy",
            response_time_ms=0,  # This is fast
            client_ip=get_client_ip(request)
        )
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(
            f"Health check failed: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        
        return Response(
            {
                "status": "error",
                "service": "billing-api",
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@log_api_request('private_endpoint')
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def private(request):
    """Private endpoint that requires authentication."""
    logger.debug(
        "Private endpoint accessed",
        extra={
            'user': str(request.user),
            'user_id': getattr(request.user, 'id', 'Unknown'),
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        user_info = {
            "user": request.user.username,
            "user_id": getattr(request.user, 'id', 'Unknown'),
            "email": getattr(request.user, 'email', 'Unknown'),
            "is_staff": getattr(request.user, 'is_staff', False),
            "authenticated": request.user.is_authenticated,
            "timestamp": timezone.now().isoformat(),
        }
        
        logger.info(
            f"Private endpoint accessed by user: {request.user.username}",
            extra={
                'user': str(request.user),
                'user_id': getattr(request.user, 'id', 'Unknown'),
                'is_staff': getattr(request.user, 'is_staff', False),
            }
        )
        
        billing_logger.info(
            "Private billing endpoint accessed",
            user=str(request.user),
            user_id=getattr(request.user, 'id', 'Unknown'),
            endpoint="private",
            client_ip=get_client_ip(request)
        )
        
        return Response(user_info)
        
    except Exception as e:
        logger.error(
            f"Private endpoint error: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'user': str(request.user),
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        
        return Response(
            {
                "error": "Internal server error",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@log_api_request('home_endpoint')
@api_view(["GET"])
@permission_classes([AllowAny])
def home(request):
    """Home endpoint providing API information."""
    logger.debug(
        "Home endpoint accessed",
        extra={
            'ip': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    try:
        api_info = {
            "message": "Welcome to the Billing API",
            "service": "billing-api",
            "version": "1.0.0",
            "timestamp": timezone.now().isoformat(),
            "endpoints": {
                "health": "/health/ - Health check endpoint",
                "private": "/private/ - Private endpoint (requires authentication)",
                "home": "/ - This endpoint"
            },
            "documentation": "/docs/ - API documentation (if available)",
            "status": "operational"
        }
        
        logger.info("Home endpoint information provided")
        api_logger.info(
            "Home endpoint accessed",
            client_ip=get_client_ip(request),
            user=str(request.user) if request.user.is_authenticated else 'Anonymous',
            endpoints_count=len(api_info["endpoints"])
        )
        
        return Response(api_info)
        
    except Exception as e:
        logger.error(
            f"Home endpoint error: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'ip': get_client_ip(request),
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            },
            exc_info=True
        )
        
        return Response(
            {
                "error": "Internal server error",
                "service": "billing-api",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@log_api_request('test_rbac_endpoint')
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test_rbac(request):
    """Test endpoint to check RBAC/ABAC functionality."""
    logger.debug(f"Test RBAC endpoint accessed by {request.user}")
    
    try:
        # Get user attributes from request
        user_attrs = getattr(request, 'user_attrs', None)
        
        # Test various permissions
        permissions_test = {
            "user": request.user.username,
            "user_id": getattr(request.user, 'id', None),
            "has_user_attrs": user_attrs is not None,
            "user_attrs": None if not user_attrs else {
                "user_id": user_attrs.user_id,
                "username": user_attrs.username,
                "email": user_attrs.email,
                "roles": user_attrs.roles,
                "department": user_attrs.department,
                "customer_ids": user_attrs.customer_ids,
                "service_specific_attrs": user_attrs.service_specific_attrs
            },
            "permissions": {
                "create_invoice": 'invoice_manager' in (user_attrs.roles if user_attrs else []),
                "billing_admin": 'billing_admin' in (user_attrs.roles if user_attrs else []),
                "view_payments": 'payment_viewer' in (user_attrs.roles if user_attrs else []),
                "customer_manager": 'customer_manager' in (user_attrs.roles if user_attrs else []),
            }
        }
        
        return Response(permissions_test)
        
    except Exception as e:
        logger.error(f"Test RBAC error: {str(e)}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@log_api_request('billing_admin_endpoint')
@api_view(["GET"])
def billing_admin_only(request):
    """Endpoint that requires billing_admin role."""
    logger.debug(f"Billing admin endpoint accessed by {request.user}")
    
    # Manual role check since we're using function-based views
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_attrs = getattr(request, 'user_attrs', None)
    if not user_attrs or 'billing_admin' not in user_attrs.roles:
        return Response({"error": "billing_admin role required"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        "message": "Access granted to billing admin endpoint",
        "user": request.user.username,
        "role": "billing_admin",
        "timestamp": timezone.now().isoformat()
    })

@log_api_request('customer_manager_endpoint')
@api_view(["GET"])
def customer_manager_only(request):
    """Endpoint that requires customer_manager role."""
    logger.debug(f"Customer manager endpoint accessed by {request.user}")
    
    # Manual role check
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_attrs = getattr(request, 'user_attrs', None)
    if not user_attrs or 'customer_manager' not in user_attrs.roles:
        return Response({"error": "customer_manager role required"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        "message": "Access granted to customer manager endpoint",
        "user": request.user.username,
        "role": "customer_manager",
        "customer_ids": user_attrs.customer_ids if user_attrs else [],
        "timestamp": timezone.now().isoformat()
    })

@log_api_request('invoice_manager_endpoint')
@api_view(["GET"])
def invoice_manager_only(request):
    """Endpoint that requires invoice_manager role."""
    logger.debug(f"Invoice manager endpoint accessed by {request.user}")
    
    # Manual role check
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_attrs = getattr(request, 'user_attrs', None)
    if not user_attrs or 'invoice_manager' not in user_attrs.roles:
        return Response({"error": "invoice_manager role required"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        "message": "Access granted to invoice manager endpoint",
        "user": request.user.username,
        "role": "invoice_manager",
        "timestamp": timezone.now().isoformat()
    })
