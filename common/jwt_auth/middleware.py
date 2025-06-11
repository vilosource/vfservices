import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.utils.deprecation import MiddlewareMixin

class JWTAuthenticationMiddleware(MiddlewareMixin):
    """Authenticate via JWT token in header or cookie."""
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
                user = User(username=payload.get('username', ''), email=payload.get('email', ''))
                user.is_active = True
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                request.user = user
            except jwt.InvalidTokenError:
                request.user = AnonymousUser()
        else:
            request.user = AnonymousUser()
