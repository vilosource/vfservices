# Phase 2: Azure RM Proxy Authentication & Security Plan

## Overview
This phase will secure the Azure RM Proxy API by integrating JWT authentication from the identity-provider and implementing role-based access control (RBAC).

## Goals
1. Require authentication for all API endpoints (except health/docs)
2. Validate JWT tokens from identity-provider
3. Implement role-based access control
4. Add security headers and rate limiting
5. Enable cross-service authentication

## Implementation Tasks

### 1. Add JWT Authentication Dependencies
Create a new file `azure-rm-proxy-server/auth.py`:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import os
from functools import lru_cache

# Import from common library
import sys
sys.path.append('/code')
from common.auth.jwt_utils import verify_jwt_token

security = HTTPBearer(auto_error=False)

@lru_cache()
def get_identity_provider_url():
    return os.getenv('IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    vf_jwt: Optional[str] = Cookie(None)
):
    # Try Authorization header first
    token = credentials.credentials if credentials else None
    
    # Fall back to cookie
    if not token:
        token = vf_jwt
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify token
    try:
        user_data = verify_jwt_token(token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return user_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )

# Optional: Get user with roles
async def get_current_user_with_roles(
    user: dict = Depends(get_current_user)
):
    # Fetch additional user data from identity provider if needed
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{get_identity_provider_url()}/api/users/{user['user_id']}/",
                headers={"Authorization": f"Bearer {user['token']}"}
            )
            if response.status_code == 200:
                user_data = response.json()
                user['roles'] = user_data.get('roles', [])
                user['permissions'] = user_data.get('permissions', [])
        except:
            # If we can't get roles, continue with basic user data
            pass
    
    return user
```

### 2. Update Main Application
Modify `azure-rm-proxy-server/azure_rm_proxy/app/main.py`:

```python
# Add imports
from .auth import get_current_user, get_current_user_with_roles
from fastapi.middleware.cors import CORSMiddleware

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', 'https://arm-proxy.maltacentral.com').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Update routes to require authentication
# Example for subscriptions endpoint:
@router.get("/api/subscriptions/")
async def list_subscriptions(
    current_user: dict = Depends(get_current_user),
    refresh: bool = Query(False),
    azure_service: AzureService = Depends(get_azure_service)
):
    # Log user access
    logger.info(f"User {current_user.get('email')} accessing subscriptions")
    
    # Existing logic...
```

### 3. Add Role-Based Access Control
Create `azure-rm-proxy-server/rbac.py`:

```python
from fastapi import HTTPException, status
from typing import List, Dict

# Define roles and their permissions
ROLE_PERMISSIONS = {
    "azure:read": [
        "subscriptions.list",
        "resource_groups.list",
        "virtual_machines.list",
        "virtual_machines.get",
        "routes.list",
        "vm_reports.list",
    ],
    "azure:write": [
        "virtual_machines.update",
        "virtual_machines.restart",
        "virtual_machines.stop",
        "virtual_machines.start",
    ],
    "azure:admin": [
        "subscriptions.create",
        "subscriptions.delete",
        "resource_groups.create",
        "resource_groups.delete",
    ]
}

def check_permission(user: Dict, required_permission: str):
    """Check if user has required permission"""
    user_roles = user.get('roles', [])
    
    # Check each role for the permission
    for role in user_roles:
        if role in ROLE_PERMISSIONS:
            if required_permission in ROLE_PERMISSIONS[role]:
                return True
    
    # Check direct permissions
    user_permissions = user.get('permissions', [])
    if required_permission in user_permissions:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Permission denied. Required: {required_permission}"
    )

# Decorator for permission checking
def require_permission(permission: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user from kwargs
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            check_permission(user, permission)
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
```

### 4. Update Docker Configuration
Add to `docker-compose.yml` for the azure-rm-proxy service:

```yaml
environment:
  # Add authentication config
  - VF_JWT_SECRET=${VF_JWT_SECRET:-change-me}
  - IDENTITY_PROVIDER_URL=http://identity-provider:8000
  - REQUIRE_AUTH=${REQUIRE_AUTH:-true}
  - ALLOWED_ORIGINS=https://arm-proxy.maltacentral.com,https://maltacentral.com,https://www.maltacentral.com
  - SSO_COOKIE_DOMAIN=.maltacentral.com
```

### 5. Update Requirements
Add to `azure-rm-proxy-server/requirements.txt`:
```
python-jose[cryptography]>=3.3.0
python-multipart>=0.0.5
```

### 6. Implement Rate Limiting
Add `azure-rm-proxy-server/rate_limiting.py`:

```python
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_interval = 60  # seconds
        asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self.cleanup_interval)
            self._cleanup_old_requests()
    
    def _cleanup_old_requests(self):
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        for key in list(self.requests.keys()):
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]
            if not self.requests[key]:
                del self.requests[key]
    
    async def check_rate_limit(self, request: Request, user: dict = None):
        # Use user ID if authenticated, otherwise use IP
        if user:
            key = f"user:{user.get('user_id', 'unknown')}"
            limit = self.requests_per_minute * 2  # Higher limit for authenticated users
        else:
            key = f"ip:{request.client.host}"
            limit = self.requests_per_minute
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        # Record request
        self.requests[key].append(now)
```

### 7. Create Security Headers Middleware
Add to main.py:

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["arm-proxy.maltacentral.com", "*.maltacentral.com"]
)
```

### 8. Update Health Check
Keep health check public (no auth required):

```python
@app.get("/api/ping", tags=["health"])
async def health_check():
    """Health check endpoint - No authentication required"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

### 9. Testing Plan
1. Create test user in identity-provider with azure:read role
2. Test authentication flow:
   - Login via maltacentral.com
   - Access arm-proxy.maltacentral.com
   - Verify JWT cookie is present
   - Test API calls with and without auth
3. Test authorization:
   - Create users with different roles
   - Verify permissions are enforced
4. Test rate limiting:
   - Make rapid requests
   - Verify 429 responses

### 10. Playwright Test Suite
Create `playwright/azure-rm-proxy/smoke-tests/test_auth.py`:

```python
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "https://arm-proxy.maltacentral.com"
LOGIN_URL = "https://www.maltacentral.com/accounts/login/"

def test_unauthenticated_access_blocked(page: Page):
    """Test that API requires authentication"""
    response = page.request.get(f"{BASE_URL}/api/subscriptions/")
    assert response.status == 401

def test_health_check_public(page: Page):
    """Test that health check doesn't require auth"""
    response = page.request.get(f"{BASE_URL}/api/ping")
    assert response.status == 200

def test_authenticated_access(page: Page):
    """Test authenticated API access"""
    # Login first
    page.goto(LOGIN_URL)
    page.fill('input[name="email"]', 'test@example.com')
    page.fill('input[name="password"]', 'testpass123')
    page.click('button[type="submit"]')
    
    # Now access API
    response = page.request.get(f"{BASE_URL}/api/subscriptions/")
    assert response.status == 200
```

## Rollout Plan

### Phase 2A - Basic Authentication (Week 1)
1. Implement JWT validation
2. Add authentication to all endpoints
3. Test with existing users
4. Deploy with REQUIRE_AUTH=false initially

### Phase 2B - Authorization (Week 2)
1. Define and implement roles
2. Add permission checks
3. Update identity-provider with new roles
4. Test role-based access

### Phase 2C - Security Hardening (Week 3)
1. Enable rate limiting
2. Add security headers
3. Configure CORS properly
4. Enable REQUIRE_AUTH=true

## Monitoring & Alerts
- Track authentication failures
- Monitor rate limit hits
- Alert on suspicious patterns
- Log all access attempts

## Rollback Plan
- Feature flags for auth enforcement
- Keep unauthenticated endpoints during transition
- Gradual rollout by endpoint
- Quick disable via environment variable

---

*Created: 2025-01-28*  
*Status: Ready for implementation*