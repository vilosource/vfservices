"""
Django REST Framework permission classes for RBAC-ABAC
"""

from typing import Optional, List, Union
import logging
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView
from django.db.models import Model
from .redis_client import get_user_attributes
from .models import UserAttributes

logger = logging.getLogger(__name__)


class ABACPermission(BasePermission):
    """
    DRF permission class that checks ABAC policies on objects.
    
    This permission class:
    - Loads user attributes from Redis
    - Maps HTTP methods to actions
    - Delegates to model's check_abac() method
    
    Usage:
        class DocumentViewSet(ModelViewSet):
            permission_classes = [ABACPermission]
            service_name = 'document_service'  # Required
    """
    
    # Default mapping of HTTP methods to actions
    METHOD_ACTION_MAP = {
        'GET': 'view',
        'HEAD': 'view',
        'OPTIONS': 'view',
        'POST': 'create',
        'PUT': 'edit',
        'PATCH': 'edit',
        'DELETE': 'delete',
    }
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Check if user has permission to access the view.
        
        This method can be used for view-level checks.
        By default, it only checks if user is authenticated.
        
        Args:
            request: DRF request object
            view: The view being accessed
            
        Returns:
            True if access allowed
        """
        # Ensure user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # For list/create endpoints, we allow access and rely on
        # queryset filtering and object-level checks
        return True
    
    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        """
        Check if user has permission to access a specific object.
        
        Args:
            request: DRF request object
            view: The view being accessed
            obj: The object being accessed
            
        Returns:
            True if access allowed
        """
        # Get service name from view
        service_name = self._get_service_name(view)
        if not service_name:
            logger.error(f"No service_name defined on view {view.__class__.__name__}")
            return False
        
        # Load user attributes from Redis
        user_attrs = self._get_user_attributes(request, service_name)
        if not user_attrs:
            logger.warning(f"No attributes found for user {request.user.id}")
            return False
        
        # Determine action from request method
        action = self._get_action(request, view)
        
        # Check if object has ABAC support
        if not hasattr(obj, 'check_abac'):
            logger.warning(
                f"Object {obj.__class__.__name__} does not support ABAC "
                f"(missing check_abac method)"
            )
            return True  # Allow if no ABAC configured
        
        # Perform ABAC check
        return obj.check_abac(user_attrs, action)
    
    def _get_service_name(self, view: APIView) -> Optional[str]:
        """
        Get service name from view.
        
        The service name can be defined as:
        1. view.service_name attribute
        2. view.get_service_name() method
        3. settings.SERVICE_NAME
        
        Args:
            view: The view to get service name from
            
        Returns:
            Service name or None
        """
        # Check view attribute
        if hasattr(view, 'service_name'):
            return view.service_name
        
        # Check view method
        if hasattr(view, 'get_service_name'):
            return view.get_service_name()
        
        # Check Django settings
        from django.conf import settings
        return getattr(settings, 'SERVICE_NAME', None)
    
    def _get_user_attributes(self, request: Request, service_name: str) -> Optional[UserAttributes]:
        """
        Get user attributes from Redis.
        
        Can be overridden to customize attribute loading.
        
        Args:
            request: DRF request
            service_name: Service name
            
        Returns:
            UserAttributes or None
        """
        # Check if attributes are already cached on request
        cache_key = f'_abac_user_attrs_{service_name}'
        if hasattr(request, cache_key):
            return getattr(request, cache_key)
        
        # Load from Redis
        user_attrs = get_user_attributes(request.user.id, service_name)
        
        # Cache on request for this request lifecycle
        if user_attrs:
            setattr(request, cache_key, user_attrs)
        
        return user_attrs
    
    def _get_action(self, request: Request, view: APIView) -> str:
        """
        Determine action name from request.
        
        Args:
            request: DRF request
            view: The view being accessed
            
        Returns:
            Action name
        """
        # Check if view explicitly defines action (e.g., ViewSet.action)
        if hasattr(view, 'action') and view.action:
            return view.action
        
        # Map HTTP method to action
        method = request.method.upper()
        return self.METHOD_ACTION_MAP.get(method, 'view')


class RoleRequired(BasePermission):
    """
    Simple role-based permission check.
    
    This is useful for endpoints that require specific roles
    regardless of object ownership.
    
    Usage:
        @permission_classes([RoleRequired('billing_admin')])
        def admin_endpoint(request):
            ...
        
        # Or in ViewSet:
        class AdminViewSet(ViewSet):
            permission_classes = [RoleRequired('admin', 'superuser')]
    """
    
    def __init__(self, *required_roles: str):
        """
        Initialize with required roles.
        
        Args:
            *required_roles: One or more role names that grant access
        """
        self.required_roles = set(required_roles)
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """Check if user has any of the required roles."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Get service name
        service_name = self._get_service_name(view)
        if not service_name:
            logger.error(f"No service_name defined for RoleRequired check")
            return False
        
        # Load user attributes
        user_attrs = get_user_attributes(request.user.id, service_name)
        if not user_attrs:
            return False
        
        # Check if user has any required role
        user_roles = set(user_attrs.roles)
        return bool(user_roles.intersection(self.required_roles))
    
    def _get_service_name(self, view: APIView) -> Optional[str]:
        """Get service name (same logic as ABACPermission)."""
        if hasattr(view, 'service_name'):
            return view.service_name
        if hasattr(view, 'get_service_name'):
            return view.get_service_name()
        from django.conf import settings
        return getattr(settings, 'SERVICE_NAME', None)


class CombinedPermission(BasePermission):
    """
    Combine multiple permission classes with AND/OR logic.
    
    Usage:
        # Require both authentication and role
        permission_classes = [CombinedPermission(
            IsAuthenticated & RoleRequired('admin')
        )]
        
        # Require either admin role or object permission
        permission_classes = [CombinedPermission(
            RoleRequired('admin') | ABACPermission()
        )]
    """
    
    def __init__(self, permission_expression):
        """
        Initialize with permission expression.
        
        Args:
            permission_expression: Expression using & and | operators
        """
        self.permission_expression = permission_expression
    
    def has_permission(self, request: Request, view: APIView) -> bool:
        """Evaluate permission expression."""
        return self._evaluate(
            self.permission_expression,
            lambda p: p.has_permission(request, view)
        )
    
    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        """Evaluate permission expression for object."""
        return self._evaluate(
            self.permission_expression,
            lambda p: p.has_object_permission(request, view, obj)
        )
    
    def _evaluate(self, expr, check_func):
        """Recursively evaluate permission expression."""
        if isinstance(expr, BasePermission):
            return check_func(expr)
        elif hasattr(expr, 'op') and hasattr(expr, 'left') and hasattr(expr, 'right'):
            left_result = self._evaluate(expr.left, check_func)
            if expr.op == '&':
                return left_result and self._evaluate(expr.right, check_func)
            elif expr.op == '|':
                return left_result or self._evaluate(expr.right, check_func)
        return False


class ServicePermission(ABACPermission):
    """
    Convenience subclass that automatically determines service name.
    
    Usage:
        # In billing_api service:
        class InvoiceViewSet(ModelViewSet):
            permission_classes = [ServicePermission]
            # service_name automatically set to 'billing_api'
    """
    
    def _get_service_name(self, view: APIView) -> Optional[str]:
        """Auto-detect service name from app label."""
        service_name = super()._get_service_name(view)
        if service_name:
            return service_name
        
        # Try to detect from app config
        if hasattr(view, 'queryset') and view.queryset is not None:
            app_label = view.queryset.model._meta.app_label
            return app_label.replace('_', '-')
        
        # Try to detect from module name
        module_parts = view.__module__.split('.')
        if len(module_parts) > 0:
            potential_service = module_parts[0]
            if potential_service in ['billing_api', 'inventory_api', 'website', 'identity_provider']:
                return potential_service.replace('_', '-')
        
        return None