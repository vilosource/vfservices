# CIELO Authentication and Access Control Guide

## Overview

CIELO (Cloud Infrastructure Engineering and Lifecycle Optimization) is the central management portal for VF Services. This guide explains the authentication system, access control mechanisms, and common troubleshooting scenarios.

## Architecture

### Authentication Stack

```
User Request
    ↓
Django Auth Middleware
    ↓
JWT Authentication Middleware (validates JWT cookies)
    ↓
Login Required Middleware (redirects to login if no auth)
    ↓
CIELO Access Middleware (checks for CIELO roles)
    ↓
View Processing
```

### Key Components

1. **Identity Provider Integration**
   - Internal URL: `http://identity-provider:8000`
   - External URL: `https://identity.vfservices.viloforge.com`
   - Handles authentication and JWT token generation

2. **JWT Cookies**
   - `jwt`: HttpOnly cookie for server-side validation
   - `jwt_token`: JavaScript-accessible for API calls
   - Domain: `.viloforge.com` (enables SSO across services)

3. **RBAC Integration**
   - Roles stored in Identity Provider
   - Cached in Redis for performance
   - Service-specific role checking

## Access Control

### Required Roles for CIELO Access

Users MUST have at least one of these roles:
- **cielo_admin**: Full administrative access to CIELO
- **cielo_user**: Standard user access to CIELO features
- **cloud_architect**: Cloud architecture and design permissions
- **cost_analyst**: Cost analysis and reporting permissions

### Access Denial Behavior

#### Improved User Experience (Login Flow)
When a user without CIELO roles attempts to login:
1. Authentication succeeds (valid credentials)
2. Login view checks CIELO roles immediately
3. If no CIELO roles found, redirects to `/accounts/access-error/`
4. Error page provides clear information and next steps

#### Legacy Protection (Middleware)
If a user somehow bypasses the login check:
1. CieloAccessMiddleware checks roles on each request
2. Users without roles are redirected to `https://www.vfservices.viloforge.com/`

This dual-layer approach ensures security while providing a better user experience.

## Implementation Details

### Middleware Configuration

In `webapp/middleware.py`:

```python
class CieloAccessMiddleware(MiddlewareMixin):
    # URLs exempt from CIELO permission check
    EXEMPT_URLS = [
        '/accounts/login/',
        '/accounts/logout/',
        '/admin/',
        '/static/',
    ]
    
    # Roles that grant CIELO access
    ALLOWED_ROLES = ['cielo_admin', 'cielo_user', 'cloud_architect', 'cost_analyst']
```

### Login View Redirect Logic

In `accounts/views.py`:

```python
# Default redirect after successful login
redirect_url = request.GET.get('next', '/')
response = HttpResponseRedirect(redirect_url)
```

### Template Configuration

Login form must preserve the `next` parameter:

```django
<form action="{% url 'accounts:login' %}{% if request.GET.next %}?next={{ request.GET.next|urlencode }}{% endif %}" method="post">
```

## Common Issues and Solutions

### Issue 1: User Sees Access Error Page

**Symptoms:**
- User logs in successfully at `https://cielo.viloforge.com/accounts/login/`
- Gets redirected to `/accounts/access-error/`

**Cause:** User lacks CIELO-specific roles

**Solution:**
```bash
# Grant cielo_admin role to user
docker compose exec identity-provider python manage.py shell
```

```python
from identity_app.models import User, Service, Role, UserRole
from django.utils import timezone

user = User.objects.get(username='admin')
cielo_service = Service.objects.get(name='cielo_website')
role = Role.objects.get(service=cielo_service, name='cielo_admin')

UserRole.objects.create(
    user=user,
    role=role,
    granted_by=User.objects.get(username='admin'),
    granted_at=timezone.now()
)
```

### Issue 2: Login Redirect Not Preserving Next Parameter

**Symptoms:**
- User accesses `/management/`, redirected to login
- After login, goes to `/` instead of `/management/`

**Cause:** Login form not preserving `next` parameter

**Solution:** Ensure login template has correct form action (see Template Configuration above)

### Issue 3: Role Changes Not Taking Effect

**Symptoms:**
- Role granted but user still can't access CIELO

**Cause:** Redis cache not updated

**Solution:** Cache is automatically refreshed on role changes, but can be forced:
```python
from common.rbac_abac.redis_client import get_redis_client
redis_client = get_redis_client()
redis_client.delete(f"user:{user_id}:cielo_website:attrs")
```

## Testing Authentication

### Manual Testing

1. **Test redirect to login:**
   ```bash
   curl -I https://cielo.viloforge.com/management/
   # Should see: Location: /accounts/login/?next=/management/
   ```

2. **Test login preserves next:**
   ```bash
   # Access login page with next parameter
   curl https://cielo.viloforge.com/accounts/login/?next=/management/
   # Verify form action includes ?next=/management/
   ```

### Automated Testing

Playwright tests available at:
`playwright/cielo-website/smoke-tests/test_login_redirect.py`

Run tests:
```bash
pytest playwright/cielo-website/smoke-tests/test_login_redirect.py -v
```

## Security Considerations

1. **JWT Security**
   - Tokens expire after 24 hours (or 1 hour without "remember me")
   - HttpOnly flag prevents JavaScript access to auth cookie
   - Secure flag ensures HTTPS-only transmission in production

2. **Role-Based Access**
   - Roles checked on every request via middleware
   - No role caching in Django session (uses Redis)
   - Immediate effect of role changes

3. **Cross-Service SSO**
   - Cookie domain `.viloforge.com` enables SSO
   - Same JWT secret across all services
   - Consistent user experience across VF Services

## Environment Variables

Key environment variables for CIELO authentication:

```bash
# JWT Configuration
VF_JWT_SECRET="your-secret-key"
SSO_COOKIE_DOMAIN=".viloforge.com"

# Service Configuration
APPLICATION_SET_DOMAIN="cielo.viloforge.com"
SERVICE_NAME="cielo_website"

# Identity Provider
IDENTITY_PROVIDER_URL="http://identity-provider:8000"
```

## Debugging Tips

1. **Check Django Logs:**
   ```bash
   docker compose logs cielo-website -f | grep -E "(CieloAccessMiddleware|Login|Access|Redirect)"
   ```

   The enhanced logging will show:
   - When users are checked for CIELO access
   - What roles the user has vs. what's required
   - Why access was granted or denied
   - Any errors during the access check

2. **Verify User Roles:**
   ```bash
   docker compose exec identity-provider python manage.py shell
   ```
   ```python
   from identity_app.models import User, UserRole
   user = User.objects.get(username='admin')
   roles = UserRole.objects.filter(user=user, role__service__name='cielo_website')
   for ur in roles:
       print(f"Role: {ur.role.name}")
   ```

3. **Check Redis Cache:**
   ```bash
   docker compose exec redis redis-cli
   GET "user:1:cielo_website:attrs"
   ```

## Related Documentation

- [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
- [RBAC-ABAC Architecture](./RBAC-ABAC-ARCHITECTURE.md)
- [RBAC-ABAC Developer Guide](./RBAC-ABAC-DEVELOPER-GUIDE.md)

## Changelog

- 2025-01-21T15:15:00Z: Initial documentation created covering CIELO authentication architecture, access control implementation, troubleshooting, and debugging tips
- 2025-01-21T15:20:00Z: Added enhanced logging examples showing improved CieloAccessMiddleware debug output
- 2025-01-21T15:35:00Z: Updated to reflect new access error page implementation for better user experience