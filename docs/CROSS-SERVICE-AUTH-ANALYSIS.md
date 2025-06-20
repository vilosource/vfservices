# Cross-Service Authentication Analysis

## Executive Summary

This document analyzes why cross-service authentication works between `website` → `billing-api` but fails between `cielo-website` → `azure-costs`. The investigation reveals that the services authenticate via the identity provider, but the key difference lies in **where and how users log in**.

## Working Authentication Flow: Website → Billing API

### How It Works

1. **User logs in at `website.vfservices.viloforge.com`**
   - Website has a dedicated login view (`/accounts/login/`)
   - Uses `IdentityProviderClient` to authenticate against identity provider
   - On successful authentication, **website sets JWT cookies** with domain `.viloforge.com`

2. **JWT Cookie Configuration in Website**
   ```python
   # website/accounts/views.py
   response.set_cookie(
       'jwt',
       result['token'],
       domain=settings.SSO_COOKIE_DOMAIN,  # ".viloforge.com"
       httponly=True,
       secure=not settings.DEBUG,
       samesite='Lax',
       max_age=cookie_max_age
   )
   ```

3. **User accesses `billing.vfservices.viloforge.com/private`**
   - Browser automatically sends JWT cookie (domain matches)
   - Billing API's JWT middleware validates the token
   - User is authenticated and can access protected resources

### Key Configuration Details

**Website Service:**
- `APPLICATION_SET_DOMAIN=vfservices.viloforge.com`
- `SSO_COOKIE_DOMAIN=.viloforge.com`
- Has authentication views that set JWT cookies
- Uses `common.jwt_auth.middleware.JWTAuthenticationMiddleware`

**Billing API Service:**
- `APPLICATION_SET_DOMAIN=vfservices.viloforge.com`
- `SSO_COOKIE_DOMAIN=.viloforge.com`
- Only validates JWT tokens (doesn't set them)
- Uses `common.jwt_auth.middleware.JWTAuthenticationMiddleware`

## Failing Authentication Flow: CIELO → Azure Costs

### Why It Fails

1. **User logs in at `cielo.viloforge.com`**
   - CIELO also uses identity provider for authentication
   - Sets JWT cookies with domain `.viloforge.com`

2. **User accesses `azure-costs.cielo.viloforge.com/api/private`**
   - Browser sends JWT cookie (domain matches)
   - Azure Costs JWT middleware receives the token
   - **BUT: Azure Costs fails to load user attributes from Redis**

### The Critical Difference

The issue is **NOT** with cookie domain configuration or JWT token sharing. Both service pairs use the same cookie domain (`.viloforge.com`). The real issue is:

**Website authenticates users and sets cookies directly**, while **CIELO appears to delegate authentication elsewhere**. When examining the logs and test results:

1. JWT tokens ARE being shared correctly between services
2. The Azure Costs service IS receiving the JWT token
3. The JWT middleware IS authenticating the user
4. **BUT the RBAC attribute loading fails**

## Root Cause Analysis

### Website → Billing Success Factors:
1. Website handles login directly via `/accounts/login/`
2. Website communicates with identity provider to get JWT token
3. Website sets JWT cookies with proper domain
4. Billing API is registered with identity provider
5. Billing API can load user RBAC attributes from Redis

### CIELO → Azure Costs Failure Points:
1. CIELO handles login (method not examined in detail)
2. CIELO sets JWT cookies with proper domain
3. Azure Costs receives JWT token correctly
4. **Azure Costs service was not initially registered with identity provider**
5. **After registration, user attributes still fail to load**

The test output shows:
```
403 Forbidden - Response content: {"detail":"Authentication credentials were not provided."}
```

This error message is misleading. The credentials (JWT token) ARE provided, but the service cannot validate them properly due to RBAC attribute loading failure.

## Key Findings

1. **Cookie Domain Configuration is Correct**
   - All services use `SSO_COOKIE_DOMAIN=.viloforge.com`
   - This allows cookie sharing across subdomains

2. **JWT Tokens are Shared Correctly**
   - Playwright tests confirm JWT cookies are set with domain `.viloforge.com`
   - The cookies are sent to Azure Costs API

3. **Service Registration is Critical**
   - Services must be registered with identity provider
   - Services need proper RBAC roles and attributes configured

4. **The Authentication Source Matters**
   - Website implements its own login that sets cookies
   - CIELO's authentication method may not be setting up RBAC properly

## Recommendations

1. **Verify CIELO's Authentication Implementation**
   - Check how CIELO authenticates users
   - Ensure it properly communicates with identity provider
   - Verify RBAC attributes are set up during login

2. **Debug Azure Costs RBAC Loading**
   - Add detailed logging to JWT middleware
   - Check Redis connectivity and data format
   - Verify user attributes are properly stored in Redis

3. **Standardize Authentication Flow**
   - All services should use the same authentication pattern
   - Consider creating a shared authentication service
   - Ensure consistent RBAC attribute management

## Technical Details

### Environment Variables Comparison

| Variable | Website/Billing | CIELO/Azure Costs |
|----------|----------------|-------------------|
| APPLICATION_SET_DOMAIN | vfservices.viloforge.com | cielo.viloforge.com |
| SSO_COOKIE_DOMAIN | .viloforge.com | .viloforge.com |
| VF_JWT_SECRET | change-me | change-me |
| IDENTITY_PROVIDER_URL | http://identity-provider:8000 | http://identity-provider:8000 |

### Middleware Stack

Both service pairs use identical JWT middleware:
```python
MIDDLEWARE = [
    # ... other middleware ...
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.jwt_auth.middleware.JWTAuthenticationMiddleware",
    # ... other middleware ...
]
```

### Service URLs

Working pair:
- Login: `https://website.vfservices.viloforge.com/accounts/login/`
- Protected: `https://billing.vfservices.viloforge.com/private`

Failing pair:
- Login: `https://cielo.viloforge.com/accounts/login/`
- Protected: `https://azure-costs.cielo.viloforge.com/api/private`

## Conclusion

The cross-service authentication failure between CIELO and Azure Costs is not due to cookie domain misconfiguration or JWT token sharing issues. The root cause appears to be related to how RBAC attributes are loaded and validated in the Azure Costs service, possibly combined with differences in how CIELO handles user authentication compared to the main website service.