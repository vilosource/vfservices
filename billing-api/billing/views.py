import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .logging_utils import log_api_request, billing_logger, api_logger, get_client_ip

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
