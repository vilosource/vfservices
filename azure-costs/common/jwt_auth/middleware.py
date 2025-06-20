import jwt
import logging
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class JWTUser:
    """A user object created from JWT token data."""
    def __init__(self, username, email, user_id=None):
        self.username = username
        self.email = email
        self.id = user_id
        self.pk = user_id
        self.is_active = True
        self.is_staff = False
        self.is_superuser = False
        self.backend = 'django.contrib.auth.backends.ModelBackend'
    
    @property
    def is_authenticated(self):
        """JWT users are always authenticated."""
        return True
    
    @property
    def is_anonymous(self):
        """JWT users are never anonymous."""
        return False
    
    def __str__(self):
        return self.username

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
                username = payload.get('username', '')
                email = payload.get('email', '')
                user_id = payload.get('user_id')
                
                # If no user_id in JWT, try to get from database
                if not user_id and username:
                    try:
                        db_user = User.objects.get(username=username)
                        user_id = db_user.id
                    except User.DoesNotExist:
                        # User not in local database - might be from another service
                        user_id = None
                
                # Create JWT user object
                user = JWTUser(username=username, email=email, user_id=user_id)
                
                request.user = user
                request._cached_user = user  # For JWT authentication
                
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
