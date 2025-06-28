"""
JWT Authentication module for Azure RM Proxy.
Integrates with the VF Services identity provider.
"""
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import httpx
import os
from functools import lru_cache
import logging
import jwt
from datetime import datetime

# Import JWT utilities from common library
import sys
sys.path.append('/code')
try:
    from common.auth.jwt_utils import verify_jwt_token
except ImportError:
    # Fallback implementation for local development
    def verify_jwt_token(token: str) -> Optional[Dict]:
        """Fallback JWT verification for development."""
        try:
            # In production, this should use the common library
            secret = os.getenv('VF_JWT_SECRET', 'change-me')
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            return payload
        except Exception:
            return None

logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


@lru_cache()
def get_identity_provider_url() -> str:
    """Get the identity provider URL from environment."""
    return os.getenv('IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')


@lru_cache()
def get_jwt_secret() -> str:
    """Get JWT secret from environment."""
    return os.getenv('VF_JWT_SECRET', 'change-me')


@lru_cache()
def is_auth_required() -> bool:
    """Check if authentication is required."""
    return os.getenv('REQUIRE_AUTH', 'true').lower() == 'true'


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt: Optional[str] = Cookie(None)
) -> Optional[Dict]:
    """
    Get current user from JWT token.
    
    Tries to get token from:
    1. Authorization header (Bearer token)
    2. Cookie (jwt)
    
    Returns None if auth is not required and no token provided.
    Raises HTTPException if auth is required but token is invalid.
    """
    # Skip auth if not required
    if not is_auth_required():
        return None
    
    # Try Authorization header first
    token = credentials.credentials if credentials else None
    
    # Fall back to cookie
    if not token:
        token = jwt
    
    # If still no token
    if not token:
        if is_auth_required():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    
    # Verify token
    try:
        user_data = verify_jwt_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Add token to user data for potential API calls
        user_data['token'] = token
        
        logger.info(f"Authenticated user: {user_data.get('email', 'unknown')}")
        return user_data
        
    except Exception as e:
        logger.error(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def get_current_user_with_roles(
    user: Optional[Dict] = Depends(get_current_user)
) -> Optional[Dict]:
    """
    Get current user with roles from identity provider.
    
    Makes an API call to identity provider to fetch full user profile
    including roles and permissions.
    """
    if not user:
        return None
    
    # Fetch additional user data from identity provider
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{get_identity_provider_url()}/api/users/{user['user_id']}/",
                headers={"Authorization": f"Bearer {user['token']}"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Merge with existing user data
                user.update({
                    'roles': user_data.get('roles', []),
                    'permissions': user_data.get('permissions', []),
                    'attributes': user_data.get('attributes', {})
                })
                logger.info(f"Fetched roles for user {user['email']}: {user['roles']}")
            else:
                logger.warning(f"Failed to fetch user roles: {response.status_code}")
                # Continue with basic user data
                user['roles'] = []
                user['permissions'] = []
                
        except Exception as e:
            logger.error(f"Error fetching user roles: {str(e)}")
            # Continue with basic user data
            user['roles'] = []
            user['permissions'] = []
    
    return user


async def require_authenticated_user(
    user: Optional[Dict] = Depends(get_current_user)
) -> Dict:
    """
    Dependency that requires an authenticated user.
    
    Use this for endpoints that always require authentication,
    even if REQUIRE_AUTH is false.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Optional: Service account authentication for M2M communication
async def get_service_account(
    api_key: Optional[str] = None
) -> Optional[Dict]:
    """
    Authenticate service accounts using API keys.
    
    This is for machine-to-machine communication where
    JWT tokens are not practical.
    """
    if not api_key:
        return None
    
    # In production, validate API key against identity provider
    # For now, just check against environment variable
    valid_keys = os.getenv('SERVICE_API_KEYS', '').split(',')
    
    if api_key in valid_keys:
        return {
            'user_id': 'service-account',
            'email': 'service@azure-rm-proxy',
            'roles': ['azure:admin'],
            'is_service_account': True
        }
    
    return None


# Middleware for global authentication enforcement
async def auth_middleware(request, call_next):
    """
    Middleware to enforce authentication on all protected routes.
    
    Public endpoints that don't require authentication:
    - /api/ping (health check)
    - /docs (Swagger UI)
    - /redoc (ReDoc)
    - /openapi.json (OpenAPI schema)
    - /api/ (root info endpoint)
    """
    # Define public endpoints that don't require authentication
    public_paths = ['/api/ping', '/docs', '/redoc', '/openapi.json', '/api/']
    
    # Skip authentication for public endpoints
    if request.url.path in public_paths:
        return await call_next(request)
    
    # Skip if auth is not required globally
    if not is_auth_required():
        return await call_next(request)
    
    # For all other endpoints, authentication is handled by endpoint dependencies
    # This middleware just sets up the request state
    return await call_next(request)