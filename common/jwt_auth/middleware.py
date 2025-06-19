import jwt
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Authenticate via JWT token in header or cookie and load RBAC/ABAC attributes."""
    
    def process_request(self, request):
        token = None
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1]
        if token is None:
            token = request.COOKIES.get('jwt')
        
        if token:
            try:
                payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
                
                # Create user object from JWT payload
                user = User(username=payload.get('username', ''), email=payload.get('email', ''))
                user.is_active = True
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                
                # Get user ID from JWT payload
                user_id = payload.get('user_id')
                if user_id:
                    user.id = user_id
                    user.pk = user_id
                else:
                    # Fallback: Try to get the user ID from database for RBAC/ABAC
                    try:
                        db_user = User.objects.get(username=user.username)
                        user.id = db_user.id
                        user.pk = db_user.pk
                    except User.DoesNotExist:
                        # User not in local database - might be from another service
                        user.id = None
                        user.pk = None
                
                request.user = user
                
                # Load RBAC/ABAC attributes if user has ID and service name is configured
                if user.id and hasattr(settings, 'SERVICE_NAME'):
                    self._load_user_attributes(request, user.id)
                else:
                    request.user_attrs = None
                    
            except jwt.InvalidTokenError as e:
                logger.debug(f"Invalid JWT token: {e}")
                request.user = AnonymousUser()
                request.user_attrs = None
        else:
            request.user = AnonymousUser()
            request.user_attrs = None
    
    def _load_user_attributes(self, request, user_id):
        """Load user attributes from Redis for RBAC/ABAC."""
        try:
            # Import here to avoid circular imports and optional dependency
            from common.rbac_abac import get_user_attributes
            
            service_name = settings.SERVICE_NAME
            start_time = None
            
            # Performance logging
            if logger.isEnabledFor(logging.DEBUG):
                import time
                start_time = time.time()
            
            # Load attributes from Redis
            user_attrs = get_user_attributes(user_id, service_name)
            request.user_attrs = user_attrs
            
            if start_time:
                elapsed = (time.time() - start_time) * 1000  # Convert to ms
                logger.debug(f"Loaded user attributes in {elapsed:.2f}ms for user {user_id}")
                
        except ImportError:
            # RBAC/ABAC not available in this service
            logger.debug("RBAC/ABAC module not available")
            request.user_attrs = None
        except Exception as e:
            # Redis connection failure or other error - fail gracefully
            logger.warning(f"Failed to load user attributes: {e}")
            request.user_attrs = None
