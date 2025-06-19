"""
Template tags for rendering menus.
"""
from django import template
from django.conf import settings
from ..services.menu_service import MenuService
import logging

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def get_menu(context, menu_name):
    """
    Fetch menu from services and return it.
    
    Usage:
        {% load menu_tags %}
        {% get_menu 'sidebar_menu' as sidebar %}
        
    Args:
        context: Template context
        menu_name: Name of the menu to fetch
        
    Returns:
        dict: Menu data
    """
    request = context.get('request')
    if not request:
        logger.warning("No request in context, cannot fetch menu")
        return {'items': []}
    
    # Get user token from cookie or session
    user_token = request.COOKIES.get('jwt_token') or request.COOKIES.get('jwt') or request.session.get('jwt_token')
    if not user_token:
        logger.warning("No JWT token found, cannot fetch menu")
        return {'items': []}
    
    try:
        menu_service = MenuService()
        menu_data = menu_service.get_menu(menu_name, user_token)
        return menu_data
    except Exception as e:
        logger.error(f"Error fetching menu '{menu_name}': {str(e)}")
        return {'items': []}


@register.inclusion_tag('webapp/components/menu_item.html', takes_context=True)
def render_menu_item(context, item):
    """
    Render a single menu item.
    
    Args:
        context: Template context
        item: Menu item dict
        
    Returns:
        dict: Context for menu item template
    """
    return {
        'item': item,
        'request': context.get('request'),
    }


@register.inclusion_tag('webapp/components/sidebar_menu.html', takes_context=True)
def render_sidebar_menu(context):
    """
    Render the complete sidebar menu.
    
    Args:
        context: Template context
        
    Returns:
        dict: Context for sidebar menu template
    """
    request = context.get('request')
    if not request:
        return {'menu': {'items': []}}
    
    # Get user token from cookie or session
    user_token = request.COOKIES.get('jwt_token') or request.COOKIES.get('jwt') or request.session.get('jwt_token')
    if not user_token:
        return {'menu': {'items': []}}
    
    try:
        menu_service = MenuService()
        menu_data = menu_service.get_menu('sidebar_menu', user_token)
        return {
            'menu': menu_data,
            'request': request,
        }
    except Exception as e:
        logger.error(f"Error rendering sidebar menu: {str(e)}")
        return {'menu': {'items': []}}