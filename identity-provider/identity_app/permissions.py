"""
Permission classes for Identity Provider Admin API
"""
from rest_framework.permissions import BasePermission
from .services import RBACService
from .models import Service


class IsIdentityAdmin(BasePermission):
    """
    Permission class that checks if user has identity_admin role
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers always have access
        if hasattr(request.user, 'is_superuser') and request.user.is_superuser:
            return True
        
        # Check for identity_admin role
        try:
            # If user attributes are already loaded by JWT middleware
            if hasattr(request, 'user_attrs') and request.user_attrs:
                roles = getattr(request.user_attrs, 'roles', [])
                return 'identity_admin' in roles
            
            # Otherwise try to get from database (for non-JWT auth)
            if hasattr(request.user, 'id') and request.user.id:
                from django.contrib.auth.models import User
                try:
                    db_user = User.objects.get(id=request.user.id)
                    identity_service = Service.objects.get(name='identity_provider')
                    user_roles = RBACService.get_user_roles(db_user, identity_service)
                    role_names = [ur.role.name for ur in user_roles]
                    return 'identity_admin' in role_names
                except (User.DoesNotExist, Service.DoesNotExist):
                    pass
            
            return False
        except Exception:
            # If we can't get attributes, deny access
            return False