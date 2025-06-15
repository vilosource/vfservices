from django.core.cache import cache
from webapp.logging_utils import get_client_ip
import logging

logger = logging.getLogger(__name__)

def check_rate_limit(request, max_attempts=5, window_minutes=15):
    """
    Check if user has exceeded login rate limit.
    
    Args:
        request: Django request object
        max_attempts: Maximum attempts allowed
        window_minutes: Time window in minutes
        
    Returns:
        bool: True if within rate limit, False if exceeded
    """
    client_ip = get_client_ip(request)
    cache_key = f"login_attempts_{client_ip}"
    
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        logger.warning(
            f"Rate limit exceeded for IP: {client_ip}",
            extra={
                'client_ip': client_ip,
                'attempts': attempts,
                'max_attempts': max_attempts,
                'window_minutes': window_minutes
            }
        )
        return False
    
    # Increment attempts
    cache.set(cache_key, attempts + 1, window_minutes * 60)
    return True

def clear_rate_limit(request):
    """Clear rate limit for successful login."""
    client_ip = get_client_ip(request)
    cache_key = f"login_attempts_{client_ip}"
    cache.delete(cache_key)