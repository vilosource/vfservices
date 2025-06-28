"""
Role-Based Access Control (RBAC) module for Azure RM Proxy.
Defines roles and permissions for Azure resource access.
"""
from fastapi import HTTPException, status, Depends
from typing import List, Dict, Optional, Callable
from functools import wraps
import logging

from .auth import get_current_user_with_roles

logger = logging.getLogger(__name__)

# Define roles and their permissions
ROLE_PERMISSIONS = {
    "azure:read": [
        # Read-only permissions
        "subscriptions.list",
        "subscriptions.get",
        "resource_groups.list",
        "resource_groups.get",
        "virtual_machines.list",
        "virtual_machines.get",
        "virtual_networks.list",
        "virtual_networks.get",
        "routes.list",
        "routes.get",
        "vm_reports.list",
        "vm_reports.get",
        "vm_hostnames.list",
        "vnet_peering.list",
    ],
    "azure:write": [
        # Write permissions (includes all read permissions)
        "virtual_machines.update",
        "virtual_machines.restart",
        "virtual_machines.stop",
        "virtual_machines.start",
        "virtual_machines.deallocate",
        "virtual_networks.update",
        "routes.update",
        "routes.create",
        "routes.delete",
    ],
    "azure:admin": [
        # Admin permissions (includes all read and write)
        "subscriptions.create",
        "subscriptions.delete",
        "resource_groups.create",
        "resource_groups.delete",
        "virtual_machines.create",
        "virtual_machines.delete",
        "virtual_networks.create",
        "virtual_networks.delete",
        "cache.clear",
        "service.configure",
    ]
}

# Inherit permissions from lower roles
ROLE_PERMISSIONS["azure:write"].extend(ROLE_PERMISSIONS["azure:read"])
ROLE_PERMISSIONS["azure:admin"].extend(ROLE_PERMISSIONS["azure:write"])


def check_permission(user: Optional[Dict], required_permission: str) -> bool:
    """
    Check if user has required permission.
    
    Args:
        user: User dictionary with roles and permissions
        required_permission: Permission string to check
        
    Returns:
        True if user has permission, False otherwise
    """
    if not user:
        return False
    
    # Service accounts have full access
    if user.get('is_service_account'):
        return True
    
    user_roles = user.get('roles', [])
    
    # Check each role for the permission
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            if required_permission in ROLE_PERMISSIONS[role]:
                return True
    
    # Check direct permissions
    user_permissions = user.get('permissions', [])
    if required_permission in user_permissions:
        return True
    
    return False


def require_permission(permission: str):
    """
    Decorator to require specific permission for an endpoint.
    
    Usage:
        @router.get("/api/virtual-machines/")
        @require_permission("virtual_machines.list")
        async def list_vms(user: Dict = Depends(get_current_user_with_roles)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from kwargs
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not check_permission(user, permission):
                logger.warning(
                    f"Permission denied for user {user.get('email', 'unknown')} - "
                    f"Required: {permission}, User roles: {user.get('roles', [])}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required: {permission}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission(["virtual_machines.list", "virtual_machines.get"])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            for permission in permissions:
                if check_permission(user, permission):
                    return await func(*args, **kwargs)
            
            logger.warning(
                f"Permission denied for user {user.get('email', 'unknown')} - "
                f"Required any of: {permissions}, User roles: {user.get('roles', [])}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required any of: {permissions}"
            )
        
        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]):
    """
    Decorator to require all of the specified permissions.
    
    Usage:
        @require_all_permissions(["virtual_machines.list", "resource_groups.list"])
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            for permission in permissions:
                if not check_permission(user, permission):
                    logger.warning(
                        f"Permission denied for user {user.get('email', 'unknown')} - "
                        f"Missing: {permission}, User roles: {user.get('roles', [])}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Missing: {permission}"
                    )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role.
    
    Usage:
        @require_role("azure:admin")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user') or kwargs.get('user')
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_roles = user.get('roles', [])
            if role not in user_roles:
                logger.warning(
                    f"Role denied for user {user.get('email', 'unknown')} - "
                    f"Required: {role}, User roles: {user_roles}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role required: {role}"
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# Permission check dependencies for use with FastAPI
async def check_read_permission(
    user: Optional[Dict] = Depends(get_current_user_with_roles)
) -> Dict:
    """Dependency to check if user has read permissions.
    
    All authenticated users are granted read access by default.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    # All authenticated users have read access
    # No need to check for specific roles
    
    return user


async def check_write_permission(
    user: Optional[Dict] = Depends(get_current_user_with_roles)
) -> Dict:
    """Dependency to check if user has write permissions."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if not any(role in user.get('roles', []) for role in ['azure:write', 'azure:admin']):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Azure write access required"
        )
    
    return user


async def check_admin_permission(
    user: Optional[Dict] = Depends(get_current_user_with_roles)
) -> Dict:
    """Dependency to check if user has admin permissions."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    if 'azure:admin' not in user.get('roles', []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Azure admin access required"
        )
    
    return user