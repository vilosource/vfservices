# JWT Authentication Troubleshooting Guide

## Common Issues and Solutions

### 🚨 Issue: "Authentication credentials were not provided"

**Symptoms:**
- API returns 401 error with this message
- User is logged into CIELO but can't access your API
- JWT cookie exists but isn't being recognized

**Diagnosis:**
```bash
# Check if JWT cookie is being sent
curl -v -b "jwt=YOUR_TOKEN" https://your-api.domain.com/api/private 2>&1 | grep Cookie

# Check JWT middleware logs
docker compose logs your-service | grep "JWT Middleware"
```

**Solutions:**

1. **Check Middleware Order**
   ```python
   # CORRECT order in settings.py
   MIDDLEWARE = [
       "corsheaders.middleware.CorsMiddleware",
       "django.middleware.security.SecurityMiddleware",
       "django.contrib.sessions.middleware.SessionMiddleware", 
       "django.middleware.common.CommonMiddleware",
       "django.middleware.csrf.CsrfViewMiddleware",
       "django.contrib.auth.middleware.AuthenticationMiddleware",
       "common.jwt_auth.middleware.JWTAuthenticationMiddleware",  # MUST be after AuthenticationMiddleware
       "django.contrib.messages.middleware.MessageMiddleware",
       "django.middleware.clickjacking.XFrameOptionsMiddleware",
   ]
   ```

2. **Verify JWT Secret**
   ```python
   # Must match identity provider
   JWT_SECRET = os.environ.get("VF_JWT_SECRET", "change-me")
   ```

3. **Check Domain Configuration**
   ```python
   # Ensure your domain is in ALLOWED_HOSTS
   ALLOWED_HOSTS = [
       f"your-api.{APPLICATION_SET_DOMAIN}",
       f".{APPLICATION_SET_DOMAIN}",  # Allows subdomains
   ]
   ```

### 🚨 Issue: DRF Authentication Classes Override

**Symptoms:**
- Middleware logs show JWT decoded successfully
- But API still returns authentication error
- Custom authentication class conflicts

**Diagnosis:**
```bash
# Check if you have REST_FRAMEWORK config
grep -n "REST_FRAMEWORK" your-api/main/settings.py
```

**Solution:**
```python
# REMOVE any REST_FRAMEWORK authentication configuration
# ❌ DON'T DO THIS:
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['custom.auth.class'],
}

# ✅ DO THIS: Don't configure authentication classes at all
# Let the middleware handle everything
```

### 🚨 Issue: RBAC Attributes Not Loading

**Symptoms:**
- User authenticates but `request.user_attrs` is None
- No role information available
- Permission checks fail

**Diagnosis:**
```bash
# Check Redis connection
docker compose logs your-service | grep "Redis"

# Check service registration
curl http://identity-provider:8000/api/services/ | jq '.[] | select(.service=="your_service_name")'
```

**Solutions:**

1. **Verify Service Registration**
   ```python
   # Check your apps.py
   def ready(self):
       from common.rbac_abac import register_service_on_startup
       register_service_on_startup()
   ```

2. **Check SERVICE_NAME**
   ```python
   # Must match your manifest.py
   SERVICE_NAME = 'your_service_name'  # In settings.py
   
   SERVICE_MANIFEST = {
       "service": "your_service_name",  # Must be identical
   }
   ```

3. **Verify Redis Configuration**
   ```python
   REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
   REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
   ```

### 🚨 Issue: CORS Errors

**Symptoms:**
- Browser console shows CORS errors
- Cross-origin requests blocked
- Preflight requests failing

**Solution:**
```python
# Add proper CORS configuration
CORS_ALLOWED_ORIGINS = [
    f"https://website.{APPLICATION_SET_DOMAIN}",
    f"https://cielo.{APPLICATION_SET_DOMAIN}",
    f"https://{APPLICATION_SET_DOMAIN}",
]

CORS_ALLOW_CREDENTIALS = True  # Required for JWT cookies

CORS_ALLOW_HEADERS = [
    'authorization',
    'content-type',
    'x-csrftoken',
    # ... other headers
]
```

### 🚨 Issue: JWT Token Expired

**Symptoms:**
- "Invalid JWT token" in logs
- Authentication worked before but stopped
- Token validation failures

**Diagnosis:**
```bash
# Decode JWT to check expiration
echo "YOUR_JWT_TOKEN" | cut -d'.' -f2 | base64 -d | jq .exp
```

**Solution:**
- User needs to log in again to get fresh token
- Check token TTL configuration in identity provider

### 🚨 Issue: Permission Denied Despite Roles

**Symptoms:**
- User has correct roles but still gets 403
- Role checks failing unexpectedly

**Diagnosis:**
```python
# Add debug logging to your view
@permission_classes([IsAuthenticated])
def my_view(request):
    user_attrs = getattr(request, 'user_attrs', None)
    print(f"User attrs: {user_attrs}")
    if user_attrs:
        roles = getattr(user_attrs, 'roles', [])
        print(f"User roles: {roles}")
```

**Solutions:**

1. **Check Role Names**
   ```python
   # Ensure role names match exactly (case-sensitive)
   allowed_roles = ['your_service_admin']  # Must match identity provider
   ```

2. **Verify Role Assignment**
   ```bash
   # Check if user has roles assigned in identity provider
   # Contact admin to assign roles
   ```

## Debugging Tools

### Enable Debug Logging

```python
# Add to settings.py for debugging
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
        },
    },
    'loggers': {
        'common.jwt_auth': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Create Debug Endpoints

```python
# Temporary debug endpoint
@api_view(['GET'])
@permission_classes([AllowAny])
def debug_auth(request):
    user_attrs = getattr(request, 'user_attrs', None)
    return Response({
        "user_authenticated": request.user.is_authenticated,
        "user_type": str(type(request.user)),
        "user_id": getattr(request.user, 'id', None),
        "username": getattr(request.user, 'username', None),
        "user_attrs": {
            "roles": getattr(user_attrs, 'roles', []) if user_attrs else None,
        } if user_attrs else None,
        "cookies": list(request.COOKIES.keys()),
    })
```

### Test Commands

```bash
# Test health endpoint (should always work)
curl https://your-api.domain.com/api/health

# Test with verbose output
curl -v -b "jwt=TOKEN" https://your-api.domain.com/api/private

# Check service logs
docker compose logs your-service --tail 50

# Check identity provider logs  
docker compose logs identity-provider --tail 50
```

## Step-by-Step Diagnostic Process

1. **Verify Basic Setup**
   - [ ] Middleware in correct order
   - [ ] JWT_SECRET configured
   - [ ] Service name matches manifest

2. **Test Health Endpoint**
   ```bash
   curl https://your-api.domain.com/api/health
   ```

3. **Test Authentication Flow**
   - [ ] Login to CIELO
   - [ ] Check JWT cookie exists
   - [ ] Try accessing private endpoint

4. **Check Logs**
   - [ ] JWT middleware logs
   - [ ] Service registration logs
   - [ ] Redis connection logs

5. **Verify RBAC**
   - [ ] Service registered with identity provider
   - [ ] User has required roles
   - [ ] Role checks in code are correct

## Getting Help

If you're still stuck:

1. **Check Working Examples**
   - billing-api (simple approach)
   - azure-costs (full RBAC integration)

2. **Review Documentation**
   - [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
   - [RBAC-ABAC Documentation](../docs/RBAC-ABAC-IMPLEMENTATION.md)

3. **Common Issues Archive**
   - [Cross-Service Auth Analysis](../docs/CROSS-SERVICE-AUTH-ANALYSIS.md)
   - [DRF Comparison](../docs/DRF-JWT-AUTHENTICATION-COMPARISON.md)

4. **Contact Team**
   - Include logs from both your service and identity provider
   - Provide JWT token (anonymized)
   - List configuration differences from working services