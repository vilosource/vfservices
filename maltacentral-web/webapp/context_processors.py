"""
Context processors for the webapp application.
"""
from django.conf import settings


def service_urls(request):
    """
    Add service URLs to the template context.
    This allows templates to access service URLs dynamically based on APPLICATION_SET_DOMAIN.
    """
    # Use APPLICATION_SET_DOMAIN if available, otherwise default to a reasonable value
    base_domain = getattr(settings, 'APPLICATION_SET_DOMAIN', 
                         getattr(settings, 'BASE_DOMAIN', 'vfservices.viloforge.com'))
    
    # Determine protocol based on request
    protocol = 'https' if request.is_secure() else 'http'
    
    return {
        'SERVICE_URLS': {
            'identity': f'{protocol}://identity.{base_domain}',
            'website': f'{protocol}://website.{base_domain}',
            'billing': f'{protocol}://billing.{base_domain}',
            'inventory': f'{protocol}://inventory.{base_domain}',
            'main': f'{protocol}://{base_domain}',
        },
        'BASE_DOMAIN': base_domain,
    }