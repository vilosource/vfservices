from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings


def identity_admin_required(view_func):
    """
    Decorator to require identity_admin role for accessing a view.
    
    Checks if the user has the identity_admin role in their JWT attributes.
    If not, returns a 403 Forbidden response.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access the admin interface.")
            # Redirect to identity provider login with next URL
            login_url = f"{settings.EXTERNAL_SERVICE_URLS['identity']}/login/?next={request.build_absolute_uri()}"
            return redirect(login_url)
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"identity_admin_required: User {request.user} authenticated, checking permissions")
        
        # For identity_admin, we need to check the user's roles in the identity_provider service
        # because identity_admin manages the identity provider itself
        try:
            from common.rbac_abac import get_user_attributes
            
            # Get the user's attributes from the identity_provider service
            # For JWTUser, we need to get the user_id from the JWT token
            user_id = getattr(request.user, 'id', None) or getattr(request.user, 'pk', None)
            
            # If no user_id on the user object, try to get it from the JWT token directly
            if not user_id:
                jwt_token = request.COOKIES.get('jwt') or request.COOKIES.get('jwt_token')
                logger.info(f"JWT token from cookies: {jwt_token[:50] if jwt_token else 'None'}...")
                if jwt_token:
                    try:
                        import jwt as pyjwt
                        payload = pyjwt.decode(jwt_token, settings.JWT_SECRET, algorithms=["HS256"])
                        user_id = payload.get('user_id')
                        logger.info(f"JWT payload: {payload}")
                        logger.info(f"Got user_id {user_id} from JWT token for user {request.user.username}")
                    except Exception as e:
                        logger.error(f"Failed to decode JWT token: {e}")
            
            logger.info(f"User ID: {user_id}, user type: {type(request.user)}")
            if not user_id:
                messages.error(request, "Unable to verify user identity.")
                logger.error(f"No user ID found for {request.user}")
                return HttpResponseForbidden("Permission denied - no user ID")
                
            # Get attributes specifically from identity_provider service
            identity_attrs = get_user_attributes(user_id, 'identity_provider')
            
            if not identity_attrs:
                messages.error(request, "Unable to verify permissions. Please try logging in again.")
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"No attributes for user {request.user.username} in identity_provider service")
                return HttpResponseForbidden("Permission denied - no user attributes")
            
            # Check for identity_admin role
            roles = identity_attrs.roles if hasattr(identity_attrs, 'roles') else []
            
            if 'identity_admin' not in roles:
                messages.error(request, "You need identity administrator privileges to access this area.")
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"User {request.user.username} missing identity_admin role in identity_provider. Has roles: {roles}")
                return HttpResponseForbidden("Permission denied - identity_admin role required")
                
        except ImportError:
            messages.error(request, "RBAC system not available.")
            return HttpResponseForbidden("Permission denied - RBAC unavailable")
        except Exception as e:
            messages.error(request, f"Error checking permissions: {str(e)}")
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error checking identity_admin permissions: {e}")
            return HttpResponseForbidden("Permission denied - error checking permissions")
            
        return view_func(request, *args, **kwargs)
    
    return wrapped_view


def identity_admin_api_required(view_func):
    """
    Decorator for API endpoints that require identity_admin role.
    
    Similar to identity_admin_required but returns JSON error responses
    suitable for AJAX calls.
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        from django.http import JsonResponse
        
        # Check if user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({
                'error': 'Authentication required'
            }, status=401)
        
        # Check for user attributes from JWT middleware
        if not hasattr(request, 'user_attrs') or not request.user_attrs:
            return JsonResponse({
                'error': 'Unable to verify permissions'
            }, status=403)
        
        # Check for identity_admin role
        roles = getattr(request.user_attrs, 'roles', [])
        if 'identity_admin' not in roles:
            return JsonResponse({
                'error': 'identity_admin role required'
            }, status=403)
            
        return view_func(request, *args, **kwargs)
    
    return wrapped_view