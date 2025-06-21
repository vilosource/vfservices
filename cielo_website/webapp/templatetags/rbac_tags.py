"""
Template tags for RBAC role checking.
"""
import sys
from pathlib import Path
from django import template
import logging

# Add common to path
common_path = Path(__file__).resolve().parent.parent.parent.parent / 'common'
if str(common_path) not in sys.path:
    sys.path.insert(0, str(common_path))

from rbac_abac.redis_client import get_user_attributes

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def user_has_role(context, role_name, service_name='cielo_website'):
    """
    Check if the current user has a specific role.
    
    Usage:
        {% load rbac_tags %}
        {% user_has_role 'identity_admin' as has_admin_role %}
        {% if has_admin_role %}...{% endif %}
        
    Args:
        context: Template context
        role_name: Name of the role to check
        service_name: Service name (default: identity_provider)
        
    Returns:
        bool: True if user has the role, False otherwise
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return False
    
    try:
        # Get user attributes for the specified service
        user_attrs = get_user_attributes(request.user.id, service_name)
        
        if not user_attrs:
            logger.debug(f"No attributes found for user {request.user.username} in {service_name}")
            return False
        
        # Check if user has the specified role
        user_roles = user_attrs.roles
        has_role = role_name in user_roles
        
        if has_role:
            logger.debug(f"User {request.user.username} has role {role_name} in {service_name}")
        
        return has_role
        
    except Exception as e:
        logger.error(
            f"Error checking role {role_name} for user {request.user.username}: {str(e)}",
            exc_info=True
        )
        return False


@register.simple_tag(takes_context=True)
def get_user_roles(context, service_name=None):
    """
    Get all roles for the current user.
    
    Usage:
        {% load rbac_tags %}
        {% get_user_roles as user_roles %}
        {% for role in user_roles %}...{% endfor %}
        
    Args:
        context: Template context
        service_name: Service name (optional, defaults to all services)
        
    Returns:
        list: List of role names
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return []
    
    try:
        if service_name:
            # Get roles for specific service
            user_attrs = get_user_attributes(request.user.id, service_name)
            if user_attrs:
                return user_attrs.roles
        else:
            # Get all roles across all services
            # For now, just check identity_provider and cielo_website
            all_roles = []
            for service in ['identity_provider', 'cielo_website']:
                user_attrs = get_user_attributes(request.user.id, service)
                if user_attrs and user_attrs.roles:
                    all_roles.extend(user_attrs.roles)
            return list(set(all_roles))  # Remove duplicates
        
        return []
        
    except Exception as e:
        logger.error(
            f"Error getting roles for user {request.user.username}: {str(e)}",
            exc_info=True
        )
        return []