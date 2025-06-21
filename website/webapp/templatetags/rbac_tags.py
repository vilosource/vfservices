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
def user_has_role(context, role_name, service_name='website'):
    """
    Check if the current user has a specific role.
    
    Usage:
        {% user_has_role 'admin' as is_admin %}
        {% if is_admin %}...{% endif %}
        
        Or for a specific service:
        {% user_has_role 'admin' 'other_service' as is_admin %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return False
    
    try:
        # Get user attributes from Redis
        user_attrs = get_user_attributes(request.user.id, service_name)
        if not user_attrs:
            logger.debug(f"No attributes found for user {request.user.username} in {service_name}")
            return False
        
        # Check if user has the role
        user_roles = user_attrs.roles
        has_role = role_name in user_roles
        
        if has_role:
            logger.debug(f"User {request.user.username} has role {role_name} in {service_name}")
        
        return has_role
        
    except Exception as e:
        logger.error(f"Error checking role {role_name} for user {request.user.username}: {str(e)}", exc_info=True)
        return False


@register.simple_tag(takes_context=True)
def get_user_roles(context, service_name='website'):
    """
    Get all roles for the current user.
    
    Usage:
        {% get_user_roles as user_roles %}
        {% for role in user_roles %}{{ role }}{% endfor %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return []
    
    try:
        user_attrs = get_user_attributes(request.user.id, service_name)
        if not user_attrs:
            return []
        
        return user_attrs.roles
        
    except Exception as e:
        logger.error(f"Error getting roles for user {request.user.username}: {str(e)}", exc_info=True)
        return []