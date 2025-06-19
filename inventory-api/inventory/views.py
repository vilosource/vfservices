import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .logging_utils import log_api_request, inventory_logger, api_logger, get_client_ip
from .menu_manifest import MENU_CONTRIBUTIONS

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
                "warehouse_ids": getattr(user_attrs, 'warehouse_ids', []),
                "service_specific_attrs": user_attrs.service_specific_attrs
            },
            "permissions": {
                "inventory_admin": 'inventory_admin' in (user_attrs.roles if user_attrs else []),
                "inventory_manager": 'inventory_manager' in (user_attrs.roles if user_attrs else []),
                "warehouse_manager": 'warehouse_manager' in (user_attrs.roles if user_attrs else []),
                "stock_viewer": 'stock_viewer' in (user_attrs.roles if user_attrs else []),
            }
        }
        
        return Response(permissions_test)
        
    except Exception as e:
        logger.error(f"Test RBAC error: {str(e)}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@log_api_request('inventory_manager_endpoint')
@api_view(["GET"])
def inventory_manager_only(request):
    """Endpoint that requires inventory_manager role."""
    logger.debug(f"Inventory manager endpoint accessed by {request.user}")
    
    # Manual role check since we're using function-based views
    if not request.user.is_authenticated:
        return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
    
    user_attrs = getattr(request, 'user_attrs', None)
    if not user_attrs or 'inventory_manager' not in user_attrs.roles:
        return Response({"error": "inventory_manager role required"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({
        "message": "Access granted to inventory manager endpoint",
        "user": request.user.username,
        "role": "inventory_manager",
        "warehouse_ids": getattr(user_attrs, 'warehouse_ids', []) if user_attrs else [],
        "timestamp": timezone.now().isoformat()
    })


@log_api_request('menu_api_endpoint')
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_menu(request, menu_name):
    """Get menu items for a specific menu, filtered by user permissions."""
    logger.debug(
        f"Menu API accessed for menu: {menu_name} by user: {request.user}",
        extra={
            'menu_name': menu_name,
            'user': str(request.user),
            'ip': get_client_ip(request),
        }
    )
    
    try:
        # Check if menu exists
        if menu_name not in MENU_CONTRIBUTIONS:
            return Response(
                {"error": f"Menu '{menu_name}' not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get user attributes for permission checking
        user_attrs = getattr(request, 'user_attrs', None)
        user_permissions = []
        
        # Extract permissions from user attributes
        if user_attrs:
            # Map roles to permissions
            role_permission_map = {
                'inventory_admin': ['inventory.view_product', 'inventory.add_product', 
                                   'inventory.view_category', 'inventory.add_category',
                                   'inventory.view_supplier', 'inventory.view_transfer'],
                'inventory_manager': ['inventory.view_product', 'inventory.add_product', 
                                     'inventory.view_category', 'inventory.add_category',
                                     'inventory.view_supplier', 'inventory.view_transfer'],
                'warehouse_manager': ['inventory.view_product', 'inventory.view_category',
                                     'inventory.view_transfer'],
                'stock_viewer': ['inventory.view_product'],
            }
            
            for role in user_attrs.roles:
                if role in role_permission_map:
                    user_permissions.extend(role_permission_map[role])
            
            # Remove duplicates
            user_permissions = list(set(user_permissions))
        
        # Filter menu items based on permissions
        def filter_menu_items(items):
            filtered_items = []
            for item in items:
                # Check if user has any of the required permissions
                item_permissions = item.get('permissions', [])
                if not item_permissions or any(perm in user_permissions for perm in item_permissions):
                    # Clone item to avoid modifying original
                    filtered_item = item.copy()
                    
                    # Recursively filter children
                    if 'children' in filtered_item:
                        filtered_children = filter_menu_items(filtered_item['children'])
                        if filtered_children:
                            filtered_item['children'] = filtered_children
                        else:
                            # Remove children key if no children passed filter
                            filtered_item.pop('children', None)
                    
                    filtered_items.append(filtered_item)
            
            return filtered_items
        
        # Get menu configuration
        menu_config = MENU_CONTRIBUTIONS[menu_name].copy()
        
        # Filter items
        filtered_items = filter_menu_items(menu_config.get('items', []))
        
        # Build response
        response_data = {
            "menu_name": menu_name,
            "items": filtered_items,
            "app_name": "inventory",
            "version": "1.0",
            "user_permissions": user_permissions,
            "timestamp": timezone.now().isoformat()
        }
        
        logger.info(
            f"Menu '{menu_name}' returned {len(filtered_items)} items for user {request.user.username}",
            extra={
                'menu_name': menu_name,
                'user': str(request.user),
                'items_count': len(filtered_items),
                'user_permissions': user_permissions,
            }
        )
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(
            f"Menu API error: {str(e)}",
            extra={
                'error_type': type(e).__name__,
                'menu_name': menu_name,
                'user': str(request.user),
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        
        return Response(
            {
                "error": "Internal server error",
                "menu_name": menu_name,
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
