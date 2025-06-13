# Authentication Architecture

This document describes the authentication and authorization architecture for the VFServices microservices platform.

## Overview

VFServices uses a **Single Sign-On (SSO) architecture** with JWT tokens:

- **Identity Provider**: Central authentication service that issues JWT tokens
- **Service Consumers**: Other microservices that validate JWT tokens for authorization

## Architecture Components

### 1. Identity Provider Service
- **URL**: `identity.vfservices.viloforge.com`
- **Purpose**: Central authentication hub
- **Authentication**: Django session-based authentication
- **Admin Access**: Standard Django admin interface
- **JWT Role**: Issues and manages JWT tokens

### 2. Consumer Services
- **Services**: Website, Billing API, Inventory API
- **Authentication**: JWT token validation
- **JWT Role**: Validate tokens issued by Identity Provider

## Authentication Flow

### Admin Authentication (Identity Provider)
```
1. Admin → identity.vfservices.viloforge.com/admin/
2. Django session-based authentication
3. Standard username/password login
4. No JWT validation (circular dependency avoided)
```

### User SSO Authentication
```
1. User → any service requiring authentication
2. Service redirects → identity.vfservices.viloforge.com/login/
3. User authenticates with Identity Provider
4. Identity Provider issues JWT token
5. JWT token stored in secure cookie (.vfservices.viloforge.com)
6. User redirected back to original service
7. Service validates JWT token via middleware
```

## Middleware Configuration

### Identity Provider (`identity-provider/main/settings.py`)
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # NO JWT middleware - uses session-based auth
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

### Consumer Services (Website, Billing, Inventory)
```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.jwt_auth.middleware.JWTAuthenticationMiddleware",  # JWT validation
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
```

## Admin User Management

### Default Admin Credentials
- **Username**: `admin`
- **Email**: `admin@viloforge.com`
- **Password**: `admin123`

### Environment Configuration
```bash
# Configurable via environment variables
ADMIN_USERNAME=${ADMIN_USERNAME:-admin}
ADMIN_EMAIL=${ADMIN_EMAIL:-admin@viloforge.com}
ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}
```

### Management Command
```bash
# Create/update admin user
docker compose exec identity-provider python manage.py create_admin

# The command automatically:
# - Creates admin user if it doesn't exist
# - Updates existing admin user with current environment settings
# - Verifies password functionality
# - Ensures proper superuser permissions
```

## JWT Token Configuration

### Shared Secret
All services use the same JWT secret for token signing/validation:
```bash
VF_JWT_SECRET=${VF_JWT_SECRET:-change-me}
```

### Cookie Configuration
```bash
SSO_COOKIE_DOMAIN=${SSO_COOKIE_DOMAIN:-.vfservices.viloforge.com}
```

### Token Properties
- **Algorithm**: HS256
- **Expiration**: 1 hour (configurable)
- **Scope**: Domain-wide (`.vfservices.viloforge.com`)
- **Security**: HttpOnly, Secure, SameSite=Lax

## Service-Specific Authentication

### Identity Provider
- **Admin Panel**: `/admin/` - Django admin interface
- **User Login**: `/login/` - SSO login page
- **API Login**: `/api/login/` - REST API endpoint
- **Logout**: `/logout/` - Clears SSO cookie

### Website Service
- **Authentication**: JWT token validation
- **User Context**: `request.user` populated by JWT middleware
- **Protection**: `@login_required` decorator works normally

### API Services (Billing, Inventory)
- **Authentication**: JWT token validation
- **API Access**: Authorization header or cookie
- **DRF Integration**: Compatible with Django REST Framework
- **Permissions**: Standard Django permissions work

## Security Features

### Cookie Security
- **HttpOnly**: Prevents XSS attacks
- **Secure**: HTTPS only transmission
- **SameSite=Lax**: CSRF protection while allowing redirects
- **Domain Scope**: Limited to `.vfservices.viloforge.com`

### Token Security
- **Short Expiration**: 1-hour token lifetime
- **Shared Secret**: Cryptographically secure secret
- **Signature Validation**: All services verify token integrity
- **User Context**: Tokens carry minimal user information

### Network Security
- **HTTPS Only**: All authentication flows encrypted
- **CORS Configuration**: Proper cross-origin restrictions
- **CSRF Protection**: Django CSRF middleware enabled

## Development vs Production

### Development Environment
```bash
# Development domains
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
SSO_COOKIE_DOMAIN=.vfservices.viloforge.com
VF_JWT_SECRET=dev-secret-change-me
```

### Production Environment
```bash
# Production security
ADMIN_USERNAME=production_admin
ADMIN_PASSWORD=secure_random_password
SSO_COOKIE_DOMAIN=.yourdomain.com
VF_JWT_SECRET=cryptographically_secure_256_bit_secret
```

## Troubleshooting

### Admin Login Issues
1. **Check logs**: `docker compose logs identity-provider`
2. **Verify user creation**: Look for "Admin user creation" in logs
3. **Test password**: Management command includes password verification
4. **Reset admin**: Run `docker compose exec identity-provider python manage.py create_admin`

### JWT Token Issues
1. **Check shared secret**: Ensure all services use same `VF_JWT_SECRET`
2. **Verify middleware**: Confirm JWT middleware in consumer services only
3. **Cookie domain**: Ensure `SSO_COOKIE_DOMAIN` is correctly set
4. **Token expiration**: Check if tokens are expired

### Common Mistakes
- ❌ **Adding JWT middleware to Identity Provider**: Causes circular authentication
- ❌ **Different JWT secrets**: Services can't validate each other's tokens
- ❌ **Wrong cookie domain**: Tokens not shared between subdomains
- ❌ **Missing HTTPS**: Secure cookies won't work over HTTP

## API Integration Examples

### Frontend JavaScript (AJAX)
```javascript
// Token automatically included from cookie
fetch('/api/billing/invoices/', {
    method: 'GET',
    credentials: 'include'  // Include cookies
})
```

### Backend API Call
```python
# Using Authorization header
headers = {
    'Authorization': f'Bearer {jwt_token}',
    'Content-Type': 'application/json'
}
response = requests.get('https://billing.vfservices.viloforge.com/api/invoices/', headers=headers)
```

### Django View Protection
```python
from django.contrib.auth.decorators import login_required

@login_required
def protected_view(request):
    # request.user is automatically populated by JWT middleware
    user = request.user  # Contains info from JWT token
    return JsonResponse({'user': user.username})
```

## Testing Authentication

### Manual Testing
```bash
# 1. Start services
docker compose up -d

# 2. Test admin login
# Open: https://identity.vfservices.viloforge.com/admin/
# Login: admin / admin123

# 3. Test SSO flow
# Open: https://website.vfservices.viloforge.com/protected-page/
# Should redirect to identity provider for authentication
```

### Automated Testing
```bash
# Test admin creation
docker compose exec identity-provider python manage.py create_admin

# Check service logs
docker compose logs identity-provider | grep -i admin
docker compose logs website | grep -i auth
```

## Migration from Previous Setup

### What Changed
1. **Removed JWT middleware** from Identity Provider
2. **Admin user creation** moved to management command
3. **Clean architecture** separation between issuer and validators

### Upgrade Steps
1. Update Identity Provider settings (remove JWT middleware)
2. Rebuild and restart services
3. Verify admin login works
4. Test SSO flow between services

This architecture provides a robust, secure, and scalable authentication system for the microservices platform while maintaining clean separation of concerns between authentication (Identity Provider) and authorization (Consumer Services).
