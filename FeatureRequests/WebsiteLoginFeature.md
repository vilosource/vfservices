# Website Login Integration with Identity Provider

## Overview

This document outlines the specification for integrating the website login functionality with the centralized identity-provider service's `/api/login` endpoint. The integration will provide centralized authentication across all VF Services while maintaining the existing user experience.

## Current Architecture Analysis

### Traefik Reverse Proxy Setup
- **Traefik v3.4**: Handles all external traffic routing and TLS termination
- **Service Routing**: Each service has its own subdomain via Traefik labels
- **URL Structure**:
  - Identity Provider: `https://identity.vfservices.viloforge.com`
  - Website: `https://website.vfservices.viloforge.com`
  - Billing API: `https://billing.vfservices.viloforge.com`
  - Inventory API: `https://inventory.vfservices.viloforge.com`
- **TLS**: Automatic HTTPS with Let's Encrypt certificates
- **Internal Communication**: Services communicate via Docker network names

### Identity Provider Service (`identity-provider`)
- **Framework**: Django REST Framework based
- **Authentication**: JWT tokens using `common.jwt_auth.utils`
- **Main Endpoint**: `/api/login/` implemented in `LoginAPIView`
- **Response**: Returns JWT token on successful authentication
- **Input**: Username/password authentication (JSON format)
- **Features**: Comprehensive logging, security features, and error handling
- **Internal URL**: `http://identity-provider:8000` (Docker network)
- **External URL**: `https://identity.vfservices.viloforge.com` (via Traefik)

### Website Service (`website`)
- **Framework**: Django application with accounts app
- **Current State**: Basic login/logout views (template rendering only)
- **Middleware**: `JWTAuthenticationMiddleware` for JWT token validation
- **Configuration**: Already configured for JWT with shared secret
- **Templates**: Material theme login form with Bootstrap styling
- **Internal URL**: `http://website:8000` (Docker network)
- **External URL**: `https://website.vfservices.viloforge.com` (via Traefik)

### Existing JWT Flow
- **Token Creation**: Identity provider creates JWT with user info
- **Token Validation**: Website middleware validates JWT from cookies/headers
- **Shared Secret**: Both services use `VF_JWT_SECRET` for token signing/verification
- **Cookie Domain**: Configured via `SSO_COOKIE_DOMAIN` environment variable

## Integration Implementation Plan

### Phase 1: Backend API Integration

#### 1. Add HTTP Client to Website

The `IdentityProviderClient` serves as an HTTP client to communicate with the identity-provider service. It acts as a **bridge** between the website service and the identity-provider service, delegating authentication instead of handling it directly.

##### What the IdentityProviderClient Does

**Primary Function**: Acts as a bridge between your website service and your identity-provider service. Instead of the website handling authentication directly, it delegates the actual credential verification to the centralized identity provider.

**Key Responsibilities**:

1. **HTTP Communication**
   - Makes HTTP POST requests to your identity-provider's `/api/login/` endpoint
   - Sends user credentials (username/password) in JSON format
   - Handles network timeouts, connection errors, and other HTTP issues

2. **Authentication Delegation**
   ```python
   # What it does internally:
   # 1. Takes username/password from website login form
   # 2. Sends POST request to: http://identity-provider:8100/api/login/
   # 3. Returns either a JWT token (success) or error message (failure)
   ```

3. **Error Handling**
   - **Service Unavailable**: When identity-provider is down
   - **Timeout Errors**: When requests take too long
   - **Invalid Credentials**: When username/password are wrong
   - **Network Issues**: Connection problems between services

4. **Logging Integration**
   - Logs all authentication attempts with your existing logging system
   - Tracks success/failure rates
   - Records client IP addresses for security monitoring

**Why It's Needed**: Without the `IdentityProviderClient`, your website would need to store user credentials in its own database, handle password hashing and validation, duplicate authentication logic across services, and manage user accounts separately for each service.

**Architecture Flow**:
```
User Login Form → Website Service → IdentityProviderClient → Identity-Provider Service
                                                          ↓
User Gets JWT Cookie ← Website Service ← JWT Token ← Identity-Provider Service
```

The client makes your website service a **consumer** of the identity-provider service, allowing centralized user management while keeping the website's existing login flow intact.

**File**: `website/accounts/identity_client.py` (new file)

```python
import requests
import logging
from django.conf import settings
from webapp.logging_utils import get_client_ip

logger = logging.getLogger(__name__)

class IdentityProviderClient:
    """Client for communicating with the identity provider service."""
    
    def __init__(self):
        self.base_url = settings.IDENTITY_PROVIDER_URL
        self.timeout = 10
        
    def authenticate_user(self, username, password, request=None):
        """
        Authenticate user via identity provider API.
        
        Args:
            username (str): User's email/username
            password (str): User's password
            request (HttpRequest, optional): For logging purposes
            
        Returns:
            dict: Authentication result with token or error
        """
        client_ip = get_client_ip(request) if request else 'Unknown'
        
        try:
            logger.info(
                f"Attempting authentication for user: {username}",
                extra={
                    'username': username,
                    'client_ip': client_ip,
                    'service': 'identity-provider'
                }
            )
            
            response = requests.post(
                f"{self.base_url}/api/login/",
                json={"username": username, "password": password},
                timeout=self.timeout,
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'VF-Website/1.0'
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(
                    f"Authentication successful for user: {username}",
                    extra={
                        'username': username,
                        'client_ip': client_ip,
                        'service': 'identity-provider'
                    }
                )
                return result
            else:
                error_detail = response.json().get("detail", "Authentication failed")
                logger.warning(
                    f"Authentication failed for user: {username} - {error_detail}",
                    extra={
                        'username': username,
                        'client_ip': client_ip,
                        'status_code': response.status_code,
                        'error': error_detail
                    }
                )
                return {"error": error_detail}
                
        except requests.Timeout:
            logger.error(
                f"Identity provider timeout for user: {username}",
                extra={'username': username, 'client_ip': client_ip}
            )
            return {"error": "Authentication service timeout"}
            
        except requests.ConnectionError:
            logger.error(
                f"Identity provider connection error for user: {username}",
                extra={'username': username, 'client_ip': client_ip}
            )
            return {"error": "Authentication service unavailable"}
            
        except requests.RequestException as e:
            logger.error(
                f"Identity provider request failed for user: {username} - {str(e)}",
                extra={'username': username, 'client_ip': client_ip, 'error': str(e)}
            )
            return {"error": "Authentication service error"}
        
        except Exception as e:
            logger.error(
                f"Unexpected error during authentication for user: {username} - {str(e)}",
                extra={'username': username, 'client_ip': client_ip, 'error': str(e)},
                exc_info=True
            )
            return {"error": "Authentication system error"}
```

#### 2. Update Website Views

**File**: `website/accounts/views.py` (modify existing)

```python
# Add imports
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from .identity_client import IdentityProviderClient

# Replace existing login_view function
@log_view_access('login_page')
@csrf_protect
@never_cache
def login_view(request: HttpRequest) -> HttpResponse:
    """Handle both GET (render form) and POST (authenticate) requests."""
    
    if request.method == "GET":
        logger.debug(
            "Login page accessed",
            extra={
                'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
                'ip': get_client_ip(request),
                'path': request.path,
                'method': request.method,
            }
        )
        
        try:
            # Check if user is already authenticated
            if request.user.is_authenticated:
                logger.info(
                    f"Already authenticated user {request.user} accessed login page",
                    extra={
                        'user': str(request.user),
                        'ip': get_client_ip(request),
                    }
                )
                return HttpResponseRedirect(reverse('webapp:dashboard'))
            
            logger.info("Rendering login template")
            response = render(request, 'accounts/login.html')
            
            logger.debug(
                "Login template rendered successfully",
                extra={
                    'status_code': 200,
                    'template': 'accounts/login.html',
                    'user': 'Anonymous',
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(
                f"Failed to render login page: {str(e)}",
                extra={
                    'template': 'accounts/login.html',
                    'error_type': type(e).__name__,
                    'user': 'Anonymous',
                    'ip': get_client_ip(request),
                },
                exc_info=True
            )
            raise
        
    elif request.method == "POST":
        username = request.POST.get("email")  # Form uses email field
        password = request.POST.get("password")
        remember_me = request.POST.get("remember")
        
        logger.info(
            f"Login attempt for user: {username}",
            extra={
                'username': username,
                'ip': get_client_ip(request),
                'remember_me': bool(remember_me),
            }
        )
        
        if not username or not password:
            logger.warning(
                "Login attempt with missing credentials",
                extra={
                    'username': username or 'Missing',
                    'password_provided': bool(password),
                    'ip': get_client_ip(request),
                }
            )
            messages.error(request, "Email and password are required")
            return render(request, 'accounts/login.html')
        
        # Authenticate via identity provider
        client = IdentityProviderClient()
        result = client.authenticate_user(username, password, request)
        
        if "error" in result:
            logger.warning(
                f"Authentication failed for user: {username} - {result['error']}",
                extra={
                    'username': username,
                    'ip': get_client_ip(request),
                    'error': result['error'],
                }
            )
            messages.error(request, result["error"])
            return render(request, 'accounts/login.html')
        
        # Authentication successful - set JWT cookie and redirect
        redirect_url = request.GET.get('next', reverse('webapp:dashboard'))
        
        logger.info(
            f"Login successful for user: {username}, redirecting to: {redirect_url}",
            extra={
                'username': username,
                'ip': get_client_ip(request),
                'redirect_url': redirect_url,
            }
        )
        
        response = HttpResponseRedirect(redirect_url)
        
        # Set JWT cookie with appropriate settings
        cookie_max_age = 86400 if remember_me else 3600  # 24 hours or 1 hour
        response.set_cookie(
            'jwt',
            result['token'],
            domain=settings.SSO_COOKIE_DOMAIN,
            httponly=True,
            secure=not settings.DEBUG,
            samesite='Lax',
            max_age=cookie_max_age
        )
        
        messages.success(request, "Login successful")
        return response

# Update logout_view function
@log_view_access('logout_page')
@csrf_protect
def logout_view(request: HttpRequest) -> HttpResponse:
    """Handle logout - clear JWT cookie."""
    
    if request.method == "POST":
        user = request.user if request.user.is_authenticated else None
        
        logger.info(
            f"Logout initiated for user: {user}",
            extra={
                'user': str(user) if user else 'Anonymous',
                'ip': get_client_ip(request),
            }
        )
        
        response = HttpResponseRedirect(reverse('accounts:login'))
        response.delete_cookie('jwt', domain=settings.SSO_COOKIE_DOMAIN)
        
        messages.success(request, "Logged out successfully")
        
        logger.info(
            f"Logout completed for user: {user}",
            extra={
                'user': str(user) if user else 'Anonymous',
                'ip': get_client_ip(request),
            }
        )
        
        return response
    
    # GET request - render logout confirmation page
    logger.debug(
        "Logout page accessed",
        extra={
            'user': str(request.user) if request.user.is_authenticated else 'Anonymous',
            'ip': get_client_ip(request),
            'path': request.path,
            'method': request.method,
        }
    )
    
    return render(request, 'accounts/logout.html')
```

#### 3. Add Configuration Settings

**File**: `website/main/settings.py` (add to existing)

```python
# Traefik-aware service URLs
# Use internal Docker network URLs for service-to-service communication
IDENTITY_PROVIDER_URL = os.environ.get(
    "IDENTITY_PROVIDER_URL", 
    "http://identity-provider:8000"  # Internal Docker network URL
)

# For JavaScript API calls (external URLs via Traefik)
EXTERNAL_SERVICE_URLS = {
    'identity': os.environ.get('IDENTITY_EXTERNAL_URL', 'https://identity.vfservices.viloforge.com'),
    'billing': os.environ.get('BILLING_EXTERNAL_URL', 'https://billing.vfservices.viloforge.com'),
    'inventory': os.environ.get('INVENTORY_EXTERNAL_URL', 'https://inventory.vfservices.viloforge.com'),
}

# Add requests to INSTALLED_APPS dependencies in requirements.txt
```

#### 4. Update Login Template

**File**: `website/accounts/templates/accounts/login.html` (modify existing)

```html
<!-- Update the form section -->
<form action="{% url 'accounts:login' %}" method="post" id="loginForm">
    {% csrf_token %}
    
    <!-- Add error/success message display -->
    {% if messages %}
        <div class="mb-3">
            {% for message in messages %}
                <div class="alert alert-{{ message.tags|default:'info' }} alert-dismissible fade show" role="alert">
                    <i class="mdi mdi-{% if message.tags == 'error' %}alert-circle{% elif message.tags == 'success' %}check-circle{% else %}information{% endif %} me-2"></i>
                    {{ message }}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            {% endfor %}
        </div>
    {% endif %}
    
    <div class="mb-2">
        <label for="emailaddress" class="form-label">Email address</label>
        <input class="form-control" type="email" id="emailaddress" name="email" required 
               placeholder="Enter your email" value="{{ request.POST.email|default:'' }}">
    </div>
    
    <div class="mb-2">
        <a href="#" class="text-muted float-end"><small>Forgot your password?</small></a>
        <label for="password" class="form-label">Password</label>
        <div class="input-group input-group-merge">
            <input type="password" id="password" name="password" class="form-control" 
                   placeholder="Enter your password" required>
            <div class="input-group-text" data-password="false">
                <span class="password-eye"></span>
            </div>
        </div>
    </div>
    
    <div class="mb-3">
        <div class="form-check">
            <input class="form-check-input" type="checkbox" id="checkbox-signin" name="remember">
            <label class="form-check-label" for="checkbox-signin">
                Remember me
            </label>
        </div>
    </div>
    
    <div class="d-grid text-center">
        <button class="btn btn-primary" type="submit" id="loginButton">
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" style="display: none;"></span>
            Log In
        </button>
    </div>
    
    <!-- Keep existing social login section -->
    <!-- ...existing social login code... -->
</form>

<!-- Add JavaScript for better UX -->
<script>
document.getElementById('loginForm').addEventListener('submit', function() {
    const button = document.getElementById('loginButton');
    const spinner = button.querySelector('.spinner-border');
    
    button.disabled = true;
    spinner.style.display = 'inline-block';
    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Logging in...';
});
</script>
```

### Phase 2: Enhanced Features

#### 1. Rate Limiting

**File**: `website/accounts/utils.py` (new file)

```python
from django.core.cache import cache
from django.http import HttpResponseTooManyRequests
from webapp.logging_utils import get_client_ip
import logging

logger = logging.getLogger(__name__)

def check_rate_limit(request, max_attempts=5, window_minutes=15):
    """
    Check if user has exceeded login rate limit.
    
    Args:
        request: Django request object
        max_attempts: Maximum attempts allowed
        window_minutes: Time window in minutes
        
    Returns:
        bool: True if within rate limit, False if exceeded
    """
    client_ip = get_client_ip(request)
    cache_key = f"login_attempts_{client_ip}"
    
    attempts = cache.get(cache_key, 0)
    
    if attempts >= max_attempts:
        logger.warning(
            f"Rate limit exceeded for IP: {client_ip}",
            extra={
                'client_ip': client_ip,
                'attempts': attempts,
                'max_attempts': max_attempts,
                'window_minutes': window_minutes
            }
        )
        return False
    
    # Increment attempts
    cache.set(cache_key, attempts + 1, window_minutes * 60)
    return True

def clear_rate_limit(request):
    """Clear rate limit for successful login."""
    client_ip = get_client_ip(request)
    cache_key = f"login_attempts_{client_ip}"
    cache.delete(cache_key)
```

#### 2. AJAX Login (Optional Enhancement)

**File**: `website/static/js/auth.js` (new file)

```javascript
/**
 * Enhanced login handling with AJAX support
 */
class LoginHandler {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.button = document.getElementById('loginButton');
        this.init();
    }
    
    init() {
        if (this.form) {
            this.form.addEventListener('submit', this.handleSubmit.bind(this));
        }
    }
    
    handleSubmit(event) {
        // For now, use standard form submission
        // Can be enhanced with AJAX in the future
        this.showLoading();
    }
    
    showLoading() {
        const spinner = this.button.querySelector('.spinner-border');
        this.button.disabled = true;
        spinner.style.display = 'inline-block';
        this.button.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Logging in...';
    }
    
    hideLoading() {
        const spinner = this.button.querySelector('.spinner-border');
        this.button.disabled = false;
        spinner.style.display = 'none';
        this.button.innerHTML = 'Log In';
    }
    
    showError(message) {
        // Add error display logic
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show';
        errorDiv.innerHTML = `
            <i class="mdi mdi-alert-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const form = this.form;
        form.insertBefore(errorDiv, form.firstChild);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    new LoginHandler();
});
```

### Phase 3: Security & Production Readiness

#### 1. Environment Configuration

**File**: `.env` (add to existing)

```bash
# Identity Provider Integration (Internal URLs for service-to-service communication)
IDENTITY_PROVIDER_URL=http://identity-provider:8000
VF_JWT_SECRET=your-shared-jwt-secret-here
SSO_COOKIE_DOMAIN=.vfservices.viloforge.com

# External URLs for JavaScript API calls (via Traefik)
IDENTITY_EXTERNAL_URL=https://identity.vfservices.viloforge.com
BILLING_EXTERNAL_URL=https://billing.vfservices.viloforge.com
INVENTORY_EXTERNAL_URL=https://inventory.vfservices.viloforge.com

# Development overrides (when not using Traefik)
# IDENTITY_PROVIDER_URL=http://localhost:8100
# SSO_COOKIE_DOMAIN=localhost
# IDENTITY_EXTERNAL_URL=http://localhost:8100
# BILLING_EXTERNAL_URL=http://localhost:8200
# INVENTORY_EXTERNAL_URL=http://localhost:8300
```

**Important Traefik Considerations**:

1. **Internal vs External URLs**: 
   - Internal URLs (`http://service-name:8000`) for server-to-server communication within Docker network
   - External URLs (`https://service.domain.com`) for browser JavaScript API calls via Traefik

2. **Cookie Domain**: 
   - Set to `.vfservices.viloforge.com` to work across all subdomains
   - Allows JWT cookies to be shared between `website.vfservices.viloforge.com` and other services

3. **CORS Configuration**: 
   - Services need to allow requests from `website.vfservices.viloforge.com`
   - Traefik handles TLS termination, so services receive HTTP internally

#### 2. CORS Configuration for Traefik Setup

Since JavaScript will make direct calls to services via Traefik, each service needs CORS configuration:

**File**: `billing-api/main/settings.py` (add to existing)

```python
# CORS configuration for Traefik routing
CORS_ALLOWED_ORIGINS = [
    "https://website.vfservices.viloforge.com",
    "http://localhost:3000",  # Development
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Ensure django-cors-headers is in INSTALLED_APPS
INSTALLED_APPS = [
    # ...existing apps...
    'corsheaders',
    # ...
]

# Ensure CORS middleware is added
MIDDLEWARE = [
    # ...
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    # ...
]
```

**File**: `inventory-api/main/settings.py` (add same CORS configuration)

**File**: `identity-provider/main/settings.py` (add same CORS configuration)

#### 3. Requirements Update

**File**: `website/requirements.txt` (add to existing)

```txt
requests>=2.31.0
```

**File**: `billing-api/requirements.txt`, `inventory-api/requirements.txt`, `identity-provider/requirements.txt` (add to existing)

```txt
django-cors-headers>=4.3.0
```

#### 3. URL Configuration

**File**: `website/accounts/urls.py` (ensure POST support)

```python
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
```

## Security Considerations

### Authentication Security
- **JWT Tokens**: Shared secret between identity provider and website
- **HTTP-Only Cookies**: Prevents XSS attacks on tokens
- **CSRF Protection**: Django CSRF middleware protects form submissions
- **Rate Limiting**: Prevents brute force attacks
- **Input Validation**: Server-side validation of all inputs

### Communication Security
- **HTTPS**: All production communication over encrypted channels
- **Timeout Handling**: Prevents hanging requests
- **Error Handling**: Graceful degradation on service failures
- **Logging**: Comprehensive audit trail for security events

### Cookie Security
- **Domain Scoping**: Cookies scoped to appropriate domain
- **Secure Flag**: HTTPS-only cookies in production
- **SameSite**: CSRF protection via SameSite attribute
- **Expiration**: Configurable token lifetime

## Integration Benefits

### Traefik Integration Advantages

1. **Service Discovery**: Automatic routing based on Docker labels
2. **TLS Termination**: Centralized SSL certificate management via Let's Encrypt
3. **Load Balancing**: Built-in load balancing for service scaling
4. **Clean URLs**: Each service gets its own subdomain (identity.vfservices.viloforge.com)
5. **Internal Network Security**: Services communicate internally without encryption overhead
6. **Centralized Routing**: Single point of entry for all external traffic

### Authentication Benefits

1. **Centralized Authentication**: Single source of truth for user credentials
2. **Consistent JWT Tokens**: Seamless authentication across all services via shared secret
3. **Cross-Subdomain Cookies**: JWT cookies work across all *.vfservices.viloforge.com subdomains
4. **Existing Infrastructure**: Leverages current JWT middleware and logging patterns
5. **Security**: Maintains existing security patterns with HTTP-only cookies
6. **Scalability**: Identity provider handles authentication for all services through Traefik
7. **Maintainability**: Centralized user management with distributed service architecture

## Testing Strategy

### Unit Tests
- Test `IdentityProviderClient` authentication flow
- Test view logic for both GET and POST requests
- Test rate limiting functionality
- Test error handling scenarios

### Integration Tests
- Test full login flow with mock identity provider
- Test JWT cookie setting and validation
- Test logout functionality
- Test CSRF protection

### End-to-End Tests
- Test actual authentication flow between services
- Test various user scenarios (valid/invalid credentials)
- Test rate limiting in practice
- Test session management across services

## Deployment Checklist

### Pre-Deployment
- [ ] Update `requirements.txt` with requests dependency
- [ ] Set environment variables for identity provider URL
- [ ] Configure shared JWT secret across services
- [ ] Set appropriate cookie domain for environment
- [ ] Test identity provider connectivity

### Post-Deployment
- [ ] Verify login flow works end-to-end
- [ ] Test logout functionality
- [ ] Verify JWT tokens are properly validated
- [ ] Check logging and monitoring
- [ ] Test rate limiting functionality

## Monitoring and Maintenance

### Logging
- Authentication attempts (success/failure)
- Identity provider communication errors
- Rate limiting events
- JWT token validation issues

### Metrics
- Login success/failure rates
- Identity provider response times
- Rate limiting triggers
- User session durations

### Alerts
- Identity provider service unavailable
- High authentication failure rates
- Rate limiting threshold exceeded
- JWT token validation errors

## JavaScript Client-Side API Integration

### Overview

In the future, JavaScript code in the browser will need to make authenticated API calls to various VF Services (billing-api, inventory-api, etc.). This section outlines how the JWT authentication will work for client-side requests.

### Architecture for JavaScript API Calls

#### Current Flow (Server-Side)
```
Browser → Website (Django) → Other Services
         ↑ JWT in Cookie    ↑ JWT in Header
```

#### Future Flow (Client-Side)
```
Browser JavaScript → Other Services (Direct API Calls)
                   ↑ JWT Token in Authorization Header
```

### Implementation Approach

#### 1. JWT Token Access from JavaScript

Since JWT tokens are stored in HTTP-only cookies (for security), JavaScript cannot directly access them. We'll need a token endpoint:

**File**: `website/accounts/views.py` (add new endpoint)

```python
@api_view(['GET'])
@csrf_protect
def get_auth_token(request):
    """Provide JWT token for JavaScript API calls."""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Extract token from cookie or regenerate if needed
    jwt_token = request.COOKIES.get('jwt')
    if not jwt_token:
        return JsonResponse({'error': 'No token available'}, status=401)
    
    try:
        # Validate token before providing it
        from common.jwt_auth.utils import decode_jwt
        payload = decode_jwt(jwt_token)
        
        return JsonResponse({
            'token': jwt_token,
            'expires_at': payload.get('exp'),
            'user': {
                'username': payload.get('username'),
                'email': payload.get('email')
            }
        })
    except Exception as e:
        return JsonResponse({'error': 'Invalid token'}, status=401)
```

#### 2. JavaScript API Client

**File**: `website/static/js/api-client.js` (new file)

```javascript
/**
 * VF Services API Client for JavaScript
 * Handles communication with services via Traefik routing
 */
class VFApiClient {
    constructor() {
        this.token = null;
        // Traefik-routed external URLs for JavaScript API calls
        this.baseUrls = {
            billing: 'https://billing.vfservices.viloforge.com/api',
            inventory: 'https://inventory.vfservices.viloforge.com/api',
            identity: 'https://identity.vfservices.viloforge.com/api'
        };
        this.init();
    }
    
    async init() {
        await this.refreshToken();
    }
    
    /**
     * Get fresh JWT token from server
     */
    async refreshToken() {
        try {
            const response = await fetch('/accounts/api/token/', {
                method: 'GET',
                credentials: 'include',  // Include cookies
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.token = data.token;
                return true;
            } else {
                console.error('Failed to get auth token');
                this.redirectToLogin();
                return false;
            }
        } catch (error) {
            console.error('Token refresh error:', error);
            return false;
        }
    }
    
    /**
     * Make authenticated API request to Traefik-routed services
     */
    async request(service, endpoint, options = {}) {
        // Ensure we have a valid token
        if (!this.token) {
            const tokenRefreshed = await this.refreshToken();
            if (!tokenRefreshed) {
                throw new Error('Authentication required');
            }
        }
        
        const url = `${this.baseUrls[service]}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
            },
            credentials: 'include'
        };
        
        const requestOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers
            }
        };
        
        try {
            const response = await fetch(url, requestOptions);
            
            // Handle token expiration
            if (response.status === 401) {
                const tokenRefreshed = await this.refreshToken();
                if (tokenRefreshed) {
                    // Retry with new token
                    requestOptions.headers['Authorization'] = `Bearer ${this.token}`;
                    return await fetch(url, requestOptions);
                } else {
                    this.redirectToLogin();
                    throw new Error('Authentication expired');
                }
            }
            
            return response;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }
    
    /**
     * Convenience methods for different HTTP verbs
     */
    async get(service, endpoint) {
        return await this.request(service, endpoint, { method: 'GET' });
    }
    
    async post(service, endpoint, data) {
        return await this.request(service, endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
    
    async put(service, endpoint, data) {
        return await this.request(service, endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }
    
    async delete(service, endpoint) {
        return await this.request(service, endpoint, { method: 'DELETE' });
    }
    
    /**
     * Utility methods
     */
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.querySelector('[name=X-CSRFToken]')?.value || '';
    }
    
    redirectToLogin() {
        window.location.href = '/accounts/login/';
    }
}

// Global API client instance
window.vfApi = new VFApiClient();
```

#### 3. API Proxy Configuration (Recommended Approach)

Instead of direct service calls, proxy API requests through the website service for better security and CORS management:

**File**: `website/main/urls.py` (add API proxy routes)

```python
from django.urls import path, include
from . import proxy_views

urlpatterns = [
    # ...existing patterns...
    
    # API proxy endpoints
    path('api/billing/', proxy_views.billing_proxy, name='billing_proxy'),
    path('api/inventory/', proxy_views.inventory_proxy, name='inventory_proxy'),
    path('api/identity/', proxy_views.identity_proxy, name='identity_proxy'),
]
```

**File**: `website/main/proxy_views.py` (new file)

```python
import requests
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json

@login_required
@csrf_exempt
def billing_proxy(request):
    """Proxy requests to billing-api service."""
    return proxy_request(request, settings.BILLING_API_URL)

@login_required
@csrf_exempt
def inventory_proxy(request):
    """Proxy requests to inventory-api service."""
    return proxy_request(request, settings.INVENTORY_API_URL)

@login_required
@csrf_exempt
def identity_proxy(request):
    """Proxy requests to identity-provider service."""
    return proxy_request(request, settings.IDENTITY_PROVIDER_URL)

def proxy_request(request, target_base_url):
    """Generic proxy function for API requests."""
    # Get JWT token from cookie
    jwt_token = request.COOKIES.get('jwt')
    if not jwt_token:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    # Build target URL
    path = request.get_full_path().replace('/api/', '/api/', 1)
    target_url = f"{target_base_url}{path}"
    
    # Prepare headers
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Content-Type': request.content_type,
        'User-Agent': 'VF-Website-Proxy/1.0'
    }
    
    # Prepare request data
    data = None
    if request.method in ['POST', 'PUT', 'PATCH']:
        data = request.body
    
    try:
        # Make proxied request
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=data,
            params=request.GET,
            timeout=30
        )
        
        # Return response
        return HttpResponse(
            response.content,
            status=response.status_code,
            content_type=response.headers.get('content-type', 'application/json')
        )
        
    except requests.RequestException as e:
        return JsonResponse({'error': 'Service unavailable'}, status=503)
```

### Usage Examples

#### Basic API Calls
```javascript
// Get billing information
const billingResponse = await vfApi.get('billing', '/invoices/');
const invoices = await billingResponse.json();

// Create inventory item
const newItem = await vfApi.post('inventory', '/items/', {
    name: 'New Item',
    quantity: 10,
    price: 29.99
});

// Update user profile
const updatedUser = await vfApi.put('identity', '/profile/', {
    first_name: 'John',
    last_name: 'Doe'
});
```

#### Error Handling
```javascript
try {
    const response = await vfApi.get('billing', '/invoices/');
    
    if (response.ok) {
        const data = await response.json();
        // Handle success
    } else {
        // Handle API error
        const error = await response.json();
        console.error('API Error:', error);
    }
} catch (error) {
    // Handle network/auth errors
    console.error('Request failed:', error);
}
```

### Security Considerations

#### 1. Token Exposure
- **Problem**: JavaScript has access to JWT token
- **Solution**: Short-lived tokens with automatic refresh
- **Additional**: Consider separate "access tokens" for JavaScript vs HTTP-only "session tokens"

#### 2. CORS Configuration
- **Current**: Services may not allow browser requests
- **Solution**: Proxy approach through website service
- **Alternative**: Configure CORS headers on all services

#### 3. XSS Protection
- **Risk**: Malicious scripts could access tokens
- **Mitigation**: Content Security Policy (CSP), input sanitization
- **Best Practice**: Regular security audits

### Alternative Approach: Direct Service Calls

If you prefer direct JavaScript-to-service calls (not recommended initially):

#### CORS Configuration Example
**File**: `billing-api/main/settings.py`

```python
CORS_ALLOWED_ORIGINS = [
    "https://website.vfservices.viloforge.com",
    "http://localhost:3000",  # Development
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

### Future Enhancements

1. **Multi-Factor Authentication**: Extend identity provider for MFA support
2. **Social Login**: Integrate OAuth providers through identity service
3. **Password Reset**: Implement password reset flow via identity provider
4. **User Registration**: Add user registration capabilities
5. **Session Management**: Advanced session handling and concurrent login limits
6. **AJAX Login**: Enhanced user experience with asynchronous login
7. **Remember Me**: Extended session duration for trusted devices
8. **WebSocket Authentication**: Real-time features with JWT authentication
9. **Mobile App Support**: JWT tokens for mobile application authentication
10. **API Rate Limiting**: Per-user rate limiting for JavaScript API calls
