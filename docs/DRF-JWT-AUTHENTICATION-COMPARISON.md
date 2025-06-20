# Django REST Framework JWT Authentication Comparison

## Overview
This document compares how billing-api and azure-costs services handle JWT authentication with Django REST Framework.

## Key Finding
**Billing-api works without DRF authentication classes, while azure-costs required them.**

## Billing-API Configuration

### What it has:
1. **JWT Middleware** in `MIDDLEWARE` setting:
   ```python
   "common.jwt_auth.middleware.JWTAuthenticationMiddleware",
   ```

2. **No REST_FRAMEWORK configuration** - The settings.py file has no REST_FRAMEWORK dict

3. **No authentication.py file** - No custom DRF authentication class

4. **Uses DRF decorators**:
   ```python
   @api_view(["GET"])
   @permission_classes([IsAuthenticated])
   def private(request):
   ```

### Why it works:
- The JWT middleware sets `request.user` before DRF processes the request
- DRF's `IsAuthenticated` permission class only checks `request.user.is_authenticated`
- Since the middleware creates a proper user object, DRF accepts it

## Azure-Costs Configuration (After Fix)

### What it has:
1. **JWT Middleware** (same as billing-api)

2. **REST_FRAMEWORK configuration**:
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'common.jwt_auth.authentication.JWTAuthentication',
       ],
       'DEFAULT_PERMISSION_CLASSES': [
           'rest_framework.permissions.IsAuthenticated',
       ],
   }
   ```

3. **Custom authentication.py** with JWTAuthentication class that:
   - Checks for cached user from middleware
   - Handles Bearer token authentication
   - Integrates with DRF's authentication system

### Why it needed the fix:
- Having `DEFAULT_AUTHENTICATION_CLASSES` configured made DRF override the middleware's authentication
- The custom JWTAuthentication class needed to respect the middleware's work

## Key Differences

| Aspect | Billing-API | Azure-Costs |
|--------|-------------|-------------|
| REST_FRAMEWORK config | None | Full configuration with defaults |
| Authentication class | None | Custom JWTAuthentication |
| DRF behavior | Uses middleware's user | Overrides with auth classes |
| Fix needed | No | Yes - auth class must check cached user |

## Recommendations

### Option 1: Standardize on Billing-API Approach (Simpler)
- Remove REST_FRAMEWORK configuration from azure-costs
- Remove authentication.py file
- Rely solely on JWT middleware
- Pros: Simpler, less code, already proven to work
- Cons: Less DRF-idiomatic, can't use DRF's authentication features

### Option 2: Standardize on Azure-Costs Approach (More DRF-compliant)
- Add REST_FRAMEWORK configuration to billing-api
- Copy the fixed authentication.py to billing-api
- Pros: More DRF-compliant, can use authentication classes
- Cons: More complex, requires the authentication class fix

### Option 3: Hybrid Approach (Recommended)
- Services that need DRF features use the full configuration
- Simple services use just the middleware
- Document which approach each service uses

## Conclusion
The billing-api's simpler approach works because it doesn't configure DRF authentication classes, so DRF doesn't override the middleware's authentication. Azure-costs needed the fix because its REST_FRAMEWORK configuration caused DRF to use its own authentication system, which wasn't aware of the JWT cookies.