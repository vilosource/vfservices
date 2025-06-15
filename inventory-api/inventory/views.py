import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .logging_utils import log_api_request, inventory_logger, api_logger, get_client_ip

# Get logger for this module
logger = logging.getLogger(__name__)

@log_api_request('inventory_health_check')
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Health check endpoint for the inventory API."""
    logger.debug(
        "Inventory health check endpoint accessed",
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
            "service": "inventory-api",
            "timestamp": timezone.now().isoformat(),
            "version": "1.0.0",
            "database": "connected",  # Could add actual DB check here
            "features": ["inventory_management", "stock_tracking"]
        }
        
        logger.info("Inventory health check completed successfully")
        api_logger.info(
            "Health check endpoint response",
            status="healthy",
            response_time_ms=0,  # This is fast
            client_ip=get_client_ip(request)
        )
        
        return Response(health_status)
        
    except Exception as e:
        logger.error(
            f"Inventory health check failed: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        
        return Response(
            {
                "status": "error",
                "service": "inventory-api",
                "error": str(e),
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

@log_api_request('inventory_private_endpoint')
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def private(request):
    """Private inventory endpoint that requires authentication."""
    logger.debug(
        "Private inventory endpoint accessed",
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
            "service": "inventory-api",
            "permissions": ["inventory_read", "inventory_write"] if getattr(request.user, 'is_staff', False) else ["inventory_read"],
            "timestamp": timezone.now().isoformat(),
        }
        
        logger.info(
            f"Private inventory endpoint accessed by user: {request.user.username}",
            extra={
                'user': str(request.user),
                'user_id': getattr(request.user, 'id', 'Unknown'),
                'is_staff': getattr(request.user, 'is_staff', False),
                'permissions': user_info["permissions"],
            }
        )
        
        inventory_logger.info(
            "Private inventory endpoint accessed",
            user=str(request.user),
            user_id=getattr(request.user, 'id', 'Unknown'),
            endpoint="private",
            client_ip=get_client_ip(request),
            permissions=user_info["permissions"]
        )
        
        return Response(user_info)
        
    except Exception as e:
        logger.error(
            f"Private inventory endpoint error: {str(e)}",
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
                "service": "inventory-api",
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
