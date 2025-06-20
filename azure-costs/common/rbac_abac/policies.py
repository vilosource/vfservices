"""
Default ABAC policies for common authorization patterns
"""

from typing import Optional, Any
from .registry import register_policy
from .models import UserAttributes


@register_policy('ownership_check')
def ownership_check(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user is the owner of the object.
    
    Expects object to have either 'owner_id' or 'owner' attribute.
    """
    if obj is None:
        return False
    
    # Check direct owner_id field
    if hasattr(obj, 'owner_id'):
        return obj.owner_id == user_attrs.user_id
    
    # Check owner relationship
    if hasattr(obj, 'owner') and hasattr(obj.owner, 'id'):
        return obj.owner.id == user_attrs.user_id
    
    return False


@register_policy('ownership_or_admin')
def ownership_or_admin(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user is the owner OR has admin role.
    
    Checks ownership first, then admin roles (both global and service-specific).
    """
    if obj is None:
        return False
    
    # Check ownership
    if ownership_check(user_attrs, obj, action):
        return True
    
    # Check global admin role
    if 'admin' in user_attrs.roles or 'superuser' in user_attrs.roles:
        return True
    
    # Check service-specific admin role
    if hasattr(obj, '_meta') and hasattr(obj._meta, 'app_label'):
        service_admin_role = f"{obj._meta.app_label}_admin"
        if service_admin_role in user_attrs.roles:
            return True
    
    return False


@register_policy('department_match')
def department_match(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user's department matches object's department.
    
    Expects both user and object to have 'department' attribute.
    """
    if obj is None:
        return False
    
    if not user_attrs.department or not hasattr(obj, 'department'):
        return False
    
    return user_attrs.department == obj.department


@register_policy('department_match_or_admin')
def department_match_or_admin(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user's department matches OR user is admin.
    """
    if obj is None:
        return False
    
    # Check department match
    if department_match(user_attrs, obj, action):
        return True
    
    # Check admin roles
    return 'admin' in user_attrs.roles or 'superuser' in user_attrs.roles


@register_policy('group_membership')
def group_membership(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user is member of object's group.
    
    Checks both admin_group_ids and regular group membership.
    """
    if obj is None:
        return False
    
    # Check if user is admin of the object's group
    if hasattr(obj, 'group_id') and obj.group_id in user_attrs.admin_group_ids:
        return True
    
    # Check regular group membership (if implemented)
    if hasattr(obj, 'group') and hasattr(obj.group, 'id'):
        if obj.group.id in user_attrs.admin_group_ids:
            return True
        
        # Check if user is regular member (would need group_ids attribute)
        group_ids = getattr(user_attrs, 'group_ids', [])
        if obj.group.id in group_ids:
            return True
    
    return False


@register_policy('public_access')
def public_access(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if object is marked as public.
    
    Checks various common field names for public status.
    """
    if obj is None:
        return False
    
    # Check various public field names
    if hasattr(obj, 'is_public') and obj.is_public:
        return True
    
    if hasattr(obj, 'public') and obj.public:
        return True
    
    if hasattr(obj, 'visibility') and obj.visibility == 'public':
        return True
    
    if hasattr(obj, 'access_level') and obj.access_level == 'public':
        return True
    
    return False


@register_policy('authenticated_only')
def authenticated_only(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access to any authenticated user.
    
    Simple policy that just checks if user attributes exist.
    """
    return user_attrs is not None and user_attrs.user_id is not None


@register_policy('admin_only')
def admin_only(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access only to admin users.
    
    Checks for admin or superuser roles.
    """
    return 'admin' in user_attrs.roles or 'superuser' in user_attrs.roles


@register_policy('service_admin')
def service_admin(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access to service-specific admin users.
    
    Checks for service_name_admin role pattern.
    """
    if obj is None:
        return False
    
    # Check global admin first
    if admin_only(user_attrs, obj, action):
        return True
    
    # Check service-specific admin
    if hasattr(obj, '_meta') and hasattr(obj._meta, 'app_label'):
        service_admin_role = f"{obj._meta.app_label}_admin"
        return service_admin_role in user_attrs.roles
    
    return False


@register_policy('owner_or_group_admin')
def owner_or_group_admin(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user owns the object OR is admin of its group.
    
    Common pattern for objects that belong to both users and groups.
    """
    if obj is None:
        return False
    
    # Check ownership
    if ownership_check(user_attrs, obj, action):
        return True
    
    # Check if user is admin of the object's group
    if hasattr(obj, 'group_id') and obj.group_id in user_attrs.admin_group_ids:
        return True
    
    if hasattr(obj, 'group') and hasattr(obj.group, 'id'):
        if obj.group.id in user_attrs.admin_group_ids:
            return True
    
    return False


@register_policy('customer_access')
def customer_access(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user has access to the customer.
    
    Checks if object's customer_id is in user's customer_ids list.
    """
    if obj is None:
        return False
    
    if hasattr(obj, 'customer_id'):
        return obj.customer_id in user_attrs.customer_ids
    
    if hasattr(obj, 'customer') and hasattr(obj.customer, 'id'):
        return obj.customer.id in user_attrs.customer_ids
    
    return False


@register_policy('document_access')
def document_access(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow access if user has explicit access to the document.
    
    Checks if document ID is in user's assigned_doc_ids list.
    """
    if obj is None:
        return False
    
    if hasattr(obj, 'id'):
        return obj.id in user_attrs.assigned_doc_ids
    
    return False


@register_policy('read_only')
def read_only(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Allow only read actions (view).
    
    Useful for restricting certain objects to read-only access.
    """
    return action in ['view', 'list', 'retrieve']


@register_policy('deny_all')
def deny_all(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
    """
    Deny all access.
    
    Useful for temporarily disabling access to certain objects.
    """
    return False


# Composite policy builder
def create_composite_policy(name: str, *policies: str, require_all: bool = True):
    """
    Create a composite policy from multiple existing policies.
    
    Args:
        name: Name for the new policy
        *policies: Names of policies to combine
        require_all: If True, all policies must pass (AND).
                    If False, any policy can pass (OR).
    
    Example:
        create_composite_policy(
            'owner_or_department_admin',
            'ownership_check',
            'department_match_or_admin',
            require_all=False
        )
    """
    @register_policy(name)
    def composite_policy(user_attrs: UserAttributes, obj: Any = None, action: str = None) -> bool:
        from .registry import get_policy
        
        results = []
        for policy_name in policies:
            policy_func = get_policy(policy_name)
            if policy_func:
                result = policy_func(user_attrs, obj, action)
                results.append(result)
                
                # Short-circuit evaluation
                if require_all and not result:
                    return False
                elif not require_all and result:
                    return True
        
        if require_all:
            return all(results) if results else False
        else:
            return any(results) if results else False
    
    # Set docstring
    composite_policy.__doc__ = f"Composite policy: {' AND ' if require_all else ' OR '}.join(policies)"
    
    return composite_policy