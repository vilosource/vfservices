# CIELO Website Authentication Documentation

## Overview

The CIELO website (`https://cielo.viloforge.com`) uses a multi-layered authentication system that integrates with the VF Services Identity Provider and enforces role-based access control.

## Authentication Flow

### 1. Login Process
- **URL**: `https://cielo.viloforge.com/accounts/login/`
- **Authentication**: Credentials are validated against the Identity Provider service
- **Process**:
  1. User submits username/password
  2. CIELO sends credentials to Identity Provider (`http://identity-provider:8000/api/login/`)
  3. Identity Provider validates and returns JWT token
  4. CIELO sets JWT cookies for cross-service SSO

### 2. Access Control Middleware

The authentication system uses a layered middleware approach:

1. **JWTAuthenticationMiddleware**: Validates JWT tokens from cookies
2. **LoginRequiredMiddleware**: Redirects unauthenticated users to login
3. **CieloAccessMiddleware**: Ensures users have CIELO-specific roles

### 3. CIELO Access Requirements

Users MUST have one of the following roles to access CIELO:
- `cielo_admin` - Full administrative access
- `cielo_user` - Standard user access
- `cloud_architect` - Cloud architecture permissions
- `cost_analyst` - Cost analysis permissions

**Important**: Users without these roles will be redirected to `https://www.vfservices.viloforge.com/`

## Cookie Configuration

Two JWT cookies are set for authentication:
- `jwt` - HttpOnly cookie for server-side authentication
- `jwt_token` - JavaScript-accessible cookie for API calls

Cookie settings:
- Domain: `.viloforge.com` (enables cross-service SSO)
- Secure: True in production
- SameSite: Lax
- Max-age: 86400 (24 hours) or 3600 (1 hour) based on "remember me"

## Login Redirect Behavior

### Default Redirect
- After successful login without a `next` parameter: Redirects to `/` (homepage)
- The form preserves the `next` parameter for proper post-login redirection

### Access Denied Behavior

#### New Behavior (Improved User Experience)
- Users without CIELO roles are redirected to `/accounts/access-error/` after login
- The error page clearly explains:
  - Why access was denied
  - What roles are required
  - User's current roles (if any)
  - How to request access
- Users can choose to go to VF Services home or logout

#### Legacy Behavior (Middleware)
- If a user somehow bypasses the login check, the middleware still redirects to `https://www.vfservices.viloforge.com/`

## Granting CIELO Access

To grant a user access to CIELO, assign them one of the required roles in the Identity Provider:

```python
# Example: Grant cielo_admin role to a user
from identity_app.models import User, Service, Role, UserRole
from django.utils import timezone

user = User.objects.get(username='username')
cielo_service = Service.objects.get(name='cielo_website')
role = Role.objects.get(service=cielo_service, name='cielo_admin')

UserRole.objects.create(
    user=user,
    role=role,
    granted_by=admin_user,
    granted_at=timezone.now()
)
```

## Troubleshooting

### User redirected to www.vfservices.viloforge.com after login
- **Cause**: User lacks CIELO-specific roles
- **Solution**: Grant one of the required roles (cielo_admin, cielo_user, cloud_architect, cost_analyst)

### Login redirect not working properly
- **Check**: Ensure the login form action includes the `next` parameter
- **Template**: `/accounts/templates/accounts/login.html` should have:
  ```django
  <form action="{% url 'accounts:login' %}{% if request.GET.next %}?next={{ request.GET.next|urlencode }}{% endif %}" method="post">
  ```

### Cannot access CIELO despite having roles
- **Check**: Redis cache may need refresh
- **Solution**: Cache is automatically refreshed on role changes, but can be manually cleared if needed

## Configuration Settings

Key settings in `main/settings.py`:
```python
# Identity Provider URL (internal Docker network)
IDENTITY_PROVIDER_URL = "http://identity-provider:8000"

# SSO Cookie Domain
SSO_COOKIE_DOMAIN = os.environ.get("SSO_COOKIE_DOMAIN", "localhost")

# Default redirect after login
DEFAULT_REDIRECT_URL = "/"

# Service name for RBAC
SERVICE_NAME = 'cielo_website'
```

## Testing

Playwright tests for login redirect functionality are available at:
`playwright/cielo-website/smoke-tests/test_login_redirect.py`

Test credentials:
- Username: `alice`
- Password: `password123`

Run tests:
```bash
pytest playwright/cielo-website/smoke-tests/test_login_redirect.py -v
```

## Changelog

- 2025-01-21T15:15:00Z: Initial documentation created explaining CIELO authentication flow, access control requirements, and troubleshooting steps
- 2025-01-21T15:20:00Z: Enhanced CieloAccessMiddleware logging for better debugging of access control issues
- 2025-01-21T15:35:00Z: Implemented user-friendly access error page for users without CIELO roles instead of external redirect