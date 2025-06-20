# JWT Authentication Quick Reference

## TL;DR - Copy This Pattern

### 1. settings.py Configuration

```python
# Add to MIDDLEWARE (ORDER MATTERS!)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware", 
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.jwt_auth.middleware.JWTAuthenticationMiddleware",  # ← ADD THIS
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# JWT Configuration
JWT_SECRET = os.environ.get("VF_JWT_SECRET", "change-me")
SERVICE_NAME = 'your_service_name'  # Must match manifest.py

# ⚠️ DON'T ADD REST_FRAMEWORK AUTHENTICATION CONFIG!
```

### 2. Basic Protected View

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # ← This is all you need!
def my_protected_view(request):
    return Response({
        "user": request.user.username,
        "user_id": request.user.id,
        "message": "You are authenticated!"
    })
```

### 3. Role-Based Access

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_view(request):
    user_attrs = getattr(request, 'user_attrs', None)
    if user_attrs:
        roles = getattr(user_attrs, 'roles', [])
        if 'your_service_admin' not in roles:
            return Response({"detail": "Admin required"}, status=403)
    else:
        return Response({"detail": "No roles found"}, status=403)
    
    return Response({"message": "Admin access granted"})
```

## Essential Files to Create

### manifest.py (Service Registration)
```python
SERVICE_MANIFEST = {
    "service": "your_service_name",
    "display_name": "Your Service",
    "roles": [
        {"name": "your_service_admin", "permissions": ["*"]},
        {"name": "your_service_viewer", "permissions": ["view"]}
    ]
}
```

### apps.py (Auto-registration)
```python
def ready(self):
    try:
        from common.rbac_abac import register_service_on_startup
        register_service_on_startup()
    except Exception as e:
        logger.error(f"Failed to register service: {e}")
```

## Testing Commands

```bash
# Test without auth (should return 401)
curl https://your-api.domain.com/api/private

# Test with JWT cookie (should work)
curl -b "jwt=TOKEN" https://your-api.domain.com/api/private
```

## What You Get For Free

✅ **Cross-service authentication** - Users logged into CIELO can access your API  
✅ **Role-based access control** - User roles loaded automatically  
✅ **Standard DRF patterns** - `@permission_classes([IsAuthenticated])` just works  
✅ **User attributes** - Access via `request.user_attrs.roles`  

## Common Mistakes to Avoid

❌ Adding REST_FRAMEWORK authentication classes  
❌ Manual authentication checks in views  
❌ Wrong middleware order  
❌ Mismatched SERVICE_NAME and manifest  

## Need Help?

- 📖 [Full Guide](./JWT-AUTHENTICATION-GUIDE.md)
- 📁 [Working Examples](../billing-api/ and ../azure-costs/)
- 🐛 [Troubleshooting](./JWT-AUTHENTICATION-GUIDE.md#troubleshooting)