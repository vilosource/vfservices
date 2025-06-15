import logging
import os
from typing import Optional
from django.shortcuts import render
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from webapp.logging_utils import log_view_access, get_client_ip

# Get logger for this module
logger = logging.getLogger(__name__)

# These are views for rendering templates in a Django application for testing and development purposes. 

@log_view_access('index_template')
def index(request: HttpRequest) -> HttpResponse:
    """
    Render the index template.
    """
    logger.debug(
        "Index template view accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        logger.info("Rendering index.html template")
        response = render(request, "index.html")
        
        logger.debug(
            "Index template rendered successfully",
            extra={
                'status_code': 200,
                'template': 'index.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to render index template: {str(e)}",
            extra={
                'template': 'index.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@log_view_access('base_template')
def base(request: HttpRequest) -> HttpResponse:
    """
    Render the base template.
    """
    logger.debug(
        "Base template view accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        logger.info("Rendering base.html template")
        response = render(request, "base.html")
        
        logger.debug(
            "Base template rendered successfully",
            extra={
                'status_code': 200,
                'template': 'base.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to render base template: {str(e)}",
            extra={
                'template': 'base.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@log_view_access('auth_template')
def auth(request: HttpRequest) -> HttpResponse:
    """
    Render the auth template.
    """
    logger.debug(
        "Auth template view accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    try:
        logger.info("Rendering auth.html template")
        response = render(request, "auth.html")
        
        logger.debug(
            "Auth template rendered successfully",
            extra={
                'status_code': 200,
                'template': 'auth.html',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(
            f"Failed to render auth template: {str(e)}",
            extra={
                'template': 'auth.html',
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise

@log_view_access('template_viewer')
def template_viewer(request: HttpRequest, template_name: Optional[str] = None) -> HttpResponse:
    """
    A utility view to render a template for testing purposes.
    This view can be used to render any template by specifying the template name in the request.
    This is useful for developers to quickly view and test templates without needing to set up a full view logic.
    Usage:

    The url /template_viewer/<template_name>/ will render the specified template.
    Example:
    /template_viewer/template_name.html will render template_name.html.
    """
    logger.debug(
        "Template viewer accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
            'requested_template': template_name,
        }
    )
    
    try:
        # This view does not require any specific logic, it simply renders the template_viewer.html.
        if template_name is None:
            logger.info("Listing all available templates")
            
            # Get a list of all templates in the templates directory
            template_dir = settings.TEMPLATES[0]['DIRS'][0]
            templates = [f for f in os.listdir(template_dir) if f.endswith('.html')]
            
            logger.debug(
                f"Found {len(templates)} template files",
                extra={
                    'template_count': len(templates),
                    'template_dir': str(template_dir),
                    'templates': templates[:10],  # Log first 10 templates to avoid spam
                }
            )
            
            # Render the template viewer with a list of available templates
            response = render(request, "template_viewer.html", {"templates": templates})
            
            logger.info(
                "Template viewer rendered successfully with template list",
                extra={
                    'template_count': len(templates),
                    'status_code': 200,
                }
            )
            
            return response
        else:
            # Ensure the template name is safe to render
            original_template_name = template_name
            template_name = template_name.strip().replace("..", "").replace("/", "").replace("\\", "")
            
            if original_template_name != template_name:
                logger.warning(
                    f"Template name sanitized: '{original_template_name}' -> '{template_name}'",
                    extra={
                        'original_template': original_template_name,
                        'sanitized_template': template_name,
                        'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                        'ip': get_client_ip(request),
                    }
                )
            
            logger.info(f"Rendering specific template: {template_name}")
            
            response = render(request, template_name)
            
            logger.info(
                f"Template '{template_name}' rendered successfully",
                extra={
                    'template': template_name,
                    'status_code': 200,
                    'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                }
            )
            
            return response
            
    except FileNotFoundError as e:
        logger.error(
            f"Template not found: {template_name}",
            extra={
                'template': template_name,
                'error_type': 'FileNotFoundError',
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            }
        )
        raise
        
    except Exception as e:
        logger.error(
            f"Failed to render template viewer: {str(e)}",
            extra={
                'template': template_name,
                'error_type': type(e).__name__,
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
            },
            exc_info=True
        )
        raise