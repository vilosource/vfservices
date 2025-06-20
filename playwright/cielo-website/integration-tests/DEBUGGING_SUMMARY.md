# Azure Costs Cross-Service Authentication Debugging Summary

## Issue
When user alice logged into CIELO website (https://cielo.viloforge.com) and tried to access Azure Costs API (https://azure-costs.cielo.viloforge.com/api/private), she received a 403 Forbidden error with "Authentication credentials were not provided."

## Root Cause
Django REST Framework was overriding the user authentication set by the JWT middleware. Even though the JWT middleware correctly decoded the token and set `request.user`, DRF's authentication system was replacing it with `AnonymousUser`.

## Key Debugging Steps

1. **Added comprehensive logging** to JWT middleware to track:
   - Cookie reception
   - JWT token decoding
   - User object creation
   - RBAC attribute loading

2. **Created debug endpoints** to isolate the issue:
   - `/api/debug-middleware` - Direct Django view (bypassed DRF)
   - `/api/debug-auth` - DRF view with AllowAny permission

3. **Discovered the authentication flow**:
   - JWT cookies were correctly shared across subdomains (domain: `.viloforge.com`)
   - JWT middleware successfully decoded tokens and created user objects
   - DRF was overriding the authentication due to its authentication classes

## Solution

1. **Updated JWT Authentication class** to check for cached user from middleware:
```python
def authenticate(self, request):
    # First check if middleware already authenticated the user
    if hasattr(request, '_cached_user') and request._cached_user:
        logger.debug(f"JWT Authentication: Using cached user from middleware: {request._cached_user}")
        return (request._cached_user, None)
```

2. **Fixed user attributes handling** in views to use `getattr` instead of dictionary methods:
```python
# Before (incorrect - UserAttributes is an object, not a dict)
roles = user_attrs.get('roles', [])

# After (correct)
roles = getattr(user_attrs, 'roles', []) if user_attrs else []
```

3. **Removed default permission classes** from specific views that needed custom authentication handling.

## Verification
After the fixes:
- Alice can successfully authenticate to Azure Costs API using JWT tokens from CIELO
- The Playwright integration test passes
- Alice's roles (`costs_manager`, `costs_admin`) are correctly loaded from RBAC system
- Cross-service authentication works as expected

## Key Learnings
1. Django REST Framework's authentication system can override middleware-set users
2. When integrating JWT authentication with DRF, ensure the authentication class cooperates with middleware
3. UserAttributes objects from RBAC system are objects, not dictionaries - use `getattr` instead of dict methods
4. Debug endpoints that bypass DRF are valuable for isolating authentication issues