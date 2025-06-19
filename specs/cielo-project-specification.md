# Cielo Project Specification

## Overview
This document specifies the implementation of the Cielo project within the vfservices microservices architecture. The project will maintain consistency with existing patterns while serving as a parallel development environment.

## Domain Configuration

### Multi-Domain Architecture
The system will support multiple domains simultaneously using a single Traefik instance and shared identity-provider:

- **Primary Domain**: vfservices.viloforge.com (existing services)
- **Cielo Domain**: cielo.viloforge.com (new services)
- **Shared Services**: 
  - identity.vfservices.viloforge.com (identity-provider - shared across domains)
  - Single Traefik instance routing both domains
  - Single Redis instance for caching
  
### Identity Provider Multi-Domain Support

The identity-provider will be configured to support both domains:

1. **Single Identity Service**: `identity.vfservices.viloforge.com` serves both domains
2. **CORS Configuration**: Allow requests from both domains
3. **Redirect URLs**: Configure allowed redirect URLs for both domains
4. **JWT Tokens**: Same JWT tokens work across both domains

### Traefik Configuration
```yaml
# Identity provider accessible from both domains
labels:
  - "traefik.http.routers.identity-provider.rule=Host(`identity.${BASE_DOMAIN}`)"
  
# Main website
labels:
  - "traefik.http.routers.website.rule=Host(`${BASE_DOMAIN}`) || Host(`www.${BASE_DOMAIN}`)"
  
# Cielo website
labels:
  - "traefik.http.routers.cielo-website.rule=Host(`cielo.${BASE_DOMAIN}`)"
```

### Authentication Flow Updates

1. User visits cielo.viloforge.com
2. If not authenticated, redirect to `identity.vfservices.viloforge.com/login?redirect_url=https://cielo.viloforge.com`
3. After login, redirect back to cielo.viloforge.com with JWT token
4. Both domains share the same user base and permissions

## Services Architecture

### 1. cielo_website
- **URL**: https://cielo.viloforge.com
- **Type**: Django web application
- **Purpose**: Main web interface for Cielo project
- **Base**: Copy structure from existing `website` service

#### Components to Copy/Adapt:
- Templates structure from `website/webapp/templates/`
- Accounts app functionality
- JWT authentication middleware
- Context processors for user/menu data
- Static file handling
- Base templates and styling

#### Key Features:
- User authentication via identity-provider
- Dashboard with dynamic menu based on permissions
- Integration with azure_costs and azure_resources APIs
- RBAC/ABAC permission checks

### 2. azure_costs
- **URL**: Internal API (accessed by cielo_website)
- **Type**: REST API microservice
- **Purpose**: Provide Azure cost data and analytics

#### Endpoints:
- `/api/costs/current` - Current month costs
- `/api/costs/history` - Historical cost data
- `/api/costs/forecast` - Cost forecasting
- `/api/costs/by-service` - Costs broken down by Azure service
- `/api/costs/by-resource-group` - Costs by resource group

### 3. azure_resources
- **URL**: Internal API (accessed by cielo_website)
- **Type**: REST API microservice
- **Purpose**: Provide Azure resource inventory and management

#### Endpoints:
- `/api/resources/list` - List all resources
- `/api/resources/by-type` - Resources grouped by type
- `/api/resources/by-resource-group` - Resources by resource group
- `/api/resources/{id}` - Individual resource details
- `/api/resources/health` - Resource health status

## Directory Structure

```
vfservices/
├── cielo_website/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── main/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── accounts/  # Copied from website
│   ├── webapp/
│   │   ├── templates/
│   │   ├── static/
│   │   ├── middleware.py
│   │   ├── context_processors.py
│   │   └── views.py
│   └── services/  # For API integrations
├── azure_costs/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── main/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── costs/
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── manifest.py
│       └── policies.py
├── azure_resources/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── main/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── resources/
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── manifest.py
│       └── policies.py
└── docker-compose.yml  # Updated with new services
```

## Implementation Steps

### Phase 1: Core Setup
1. Create cielo_website Django project structure
2. Copy and adapt templates from website
3. Copy and adapt accounts app with JWT authentication
4. Configure basic routing and middleware

### Phase 2: Service Integration
1. Update docker-compose.yml with new services
2. Configure Traefik routing for cielo.viloforge.com
3. Set up internal networking for API communication
4. Implement service discovery for API endpoints

### Phase 3: API Services
1. Create azure_costs API structure
2. Create azure_resources API structure
3. Implement basic endpoints
4. Add authentication/authorization checks

### Phase 4: RBAC/ABAC Configuration
1. Define policies for new services in manifest.py files
2. Create roles specific to Cielo project
3. Configure menu items for different user roles
4. Test permission boundaries

## Docker Compose Strategy

Since Cielo is part of the vfservices ecosystem and shares the same identity-provider, Redis, and Traefik infrastructure, we have two options:

### Option 1: Single docker-compose.yml (Recommended)
Add the Cielo services to the existing `docker-compose.yml`. This ensures:
- Shared network with existing services
- Access to identity-provider without additional configuration
- Unified deployment and management
- Consistent with current architecture

### Option 2: Separate docker-compose.cielo.yml
Create a separate compose file that can be used with Docker Compose's multiple file feature:
```bash
docker-compose -f docker-compose.yml -f docker-compose.cielo.yml up
```

**Recommendation**: Use Option 1 - add to the existing docker-compose.yml since Cielo services need to interact with the core identity-provider and share the same Traefik routing.

## Docker Compose Configuration

```yaml
# Addition to existing docker-compose.yml

  cielo_website:
    build: ./cielo_website
    volumes:
      - ./cielo_website:/app
      - ./common:/app/common
    environment:
      - DJANGO_SECRET_KEY=${CIELO_WEBSITE_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - IDENTITY_PROVIDER_URL=http://identity-provider:8000
      - AZURE_COSTS_URL=http://azure-costs:8000
      - AZURE_RESOURCES_URL=http://azure-resources:8000
      - REDIS_HOST=redis
    depends_on:
      - identity-provider
      - redis
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.cielo-website.rule=Host(`cielo.${BASE_DOMAIN}`)"
      - "traefik.http.routers.cielo-website.tls=true"
      - "traefik.http.routers.cielo-website.tls.certresolver=myresolver"

  azure_costs:
    build: ./azure_costs
    volumes:
      - ./azure_costs:/app
      - ./common:/app/common
    environment:
      - DJANGO_SECRET_KEY=${AZURE_COSTS_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_HOST=redis
    depends_on:
      - redis

  azure_resources:
    build: ./azure_resources
    volumes:
      - ./azure_resources:/app
      - ./common:/app/common
    environment:
      - DJANGO_SECRET_KEY=${AZURE_RESOURCES_SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - REDIS_HOST=redis
    depends_on:
      - redis
```

## Authentication Flow

With the multi-domain setup, authentication works as follows:

1. User visits cielo.viloforge.com
2. If not authenticated, redirect to `identity.vfservices.viloforge.com/login?redirect_url=https://cielo.viloforge.com`
3. After successful login, JWT token is stored in session
4. All API calls include JWT token in Authorization header
5. APIs validate token with identity-provider
6. RBAC/ABAC policies are evaluated for each request

### Identity Provider Modifications Required

The identity-provider requires minimal updates to support multi-domain:

#### 1. Settings Configuration
```python
# identity-provider/main/settings.py

# CORS configuration
CORS_ALLOWED_ORIGINS = [
    "https://vfservices.viloforge.com",
    "https://www.vfservices.viloforge.com",
    "https://cielo.viloforge.com",
]

# Allowed redirect URLs
ALLOWED_REDIRECT_DOMAINS = [
    "vfservices.viloforge.com",
    "www.vfservices.viloforge.com", 
    "cielo.viloforge.com",
]

# Session cookie domain (allows subdomain sharing)
SESSION_COOKIE_DOMAIN = ".viloforge.com"
```

#### 2. Login View Update
```python
# identity-provider/identity_app/views.py

def login_view(request):
    redirect_url = request.GET.get('redirect_url', '')
    
    # Validate redirect URL against allowed domains
    if redirect_url:
        parsed_url = urlparse(redirect_url)
        if parsed_url.netloc not in settings.ALLOWED_REDIRECT_DOMAINS:
            redirect_url = f"https://{settings.BASE_DOMAIN}"
    
    # Rest of login logic...
```

#### 3. No Database Changes Required
- User accounts remain the same
- Permissions work across both domains
- No new models or migrations needed

#### 4. Environment Variable
```bash
# .env
BASE_DOMAIN=vfservices.viloforge.com  # Keep as-is, both domains share this base
```

**Summary**: Only configuration changes needed, no structural modifications to identity-provider.

## RBAC-Based Access Control for Cielo

### Restricting Access to Cielo Domain

The Cielo project can be restricted to specific users using RBAC:

#### 1. Create Cielo-Specific Permission
```python
# identity-provider/identity_app/models.py
# Add to existing permissions
CIELO_ACCESS = "cielo.access"  # Base permission to access Cielo domain
```

#### 2. Cielo Website Middleware
```python
# cielo_website/webapp/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from common.rbac_abac.services import PermissionService

class CieloAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip check for login/logout pages
        if request.path in ['/accounts/login/', '/accounts/logout/']:
            return self.get_response(request)
        
        # Check if user has Cielo access permission
        if request.user.is_authenticated:
            permission_service = PermissionService()
            if not permission_service.user_has_permission(
                request.user.id, 
                'cielo.access'
            ):
                messages.error(
                    request, 
                    "You don't have permission to access Cielo."
                )
                return redirect('https://vfservices.viloforge.com')
        
        return self.get_response(request)
```

#### 3. Role Configuration
```python
# Create roles for Cielo access
CIELO_ROLES = {
    "cielo_user": {
        "name": "Cielo User",
        "permissions": [
            "cielo.access",
            "azure_costs.view_costs",
            "azure_resources.view_resources"
        ]
    },
    "cielo_admin": {
        "name": "Cielo Administrator", 
        "permissions": [
            "cielo.access",
            "azure_costs.view_costs",
            "azure_costs.view_detailed_costs",
            "azure_costs.manage_budgets",
            "azure_resources.view_resources",
            "azure_resources.manage_resources"
        ]
    }
}
```

#### 4. User Assignment Examples
```python
# Only users with cielo_user or cielo_admin role can access cielo.viloforge.com
# Regular vfservices.viloforge.com users without these roles will be redirected
```

### Benefits of RBAC-Controlled Access
1. **Selective Access**: Only authorized users can access Cielo
2. **Granular Permissions**: Different permission levels within Cielo
3. **Easy Management**: Add/remove access through role assignment
4. **Audit Trail**: Track who has access to Cielo services
5. **No Separate Login**: Same identity system, just permission-based

## RBAC/ABAC Policy Examples

### azure_costs/costs/policies.py
```python
from common.rbac_abac.decorators import require_permission

# Permission definitions
VIEW_COSTS = "azure_costs.view_costs"
VIEW_DETAILED_COSTS = "azure_costs.view_detailed_costs"
MANAGE_COST_BUDGETS = "azure_costs.manage_budgets"
```

### azure_resources/resources/policies.py
```python
from common.rbac_abac.decorators import require_permission

# Permission definitions
VIEW_RESOURCES = "azure_resources.view_resources"
MANAGE_RESOURCES = "azure_resources.manage_resources"
DELETE_RESOURCES = "azure_resources.delete_resources"
```

## Menu System Integration

The Cielo project will leverage the existing vfservices menu system that provides dynamic, permission-based navigation. The menu system consists of:

### Menu Service Architecture
1. **Menu Service API**: Each microservice registers its menu items via a manifest
2. **Redis Caching**: Menu structure is cached for performance
3. **Permission Filtering**: Menu items are filtered based on user's RBAC/ABAC permissions
4. **Context Processor**: Injects menu data into all template contexts

### Menu Registration

Each service must provide a `menu_manifest.py` file that registers its menu items:

#### cielo_website/webapp/menu_manifest.py
```python
def get_menu_items():
    return {
        "service": "cielo_website",
        "items": [
            {
                "label": "Dashboard",
                "url": "/",
                "icon": "fas fa-home",
                "order": 1
            }
        ]
    }
```

#### azure_costs/costs/menu_manifest.py
```python
def get_menu_items():
    return {
        "service": "azure_costs",
        "items": [
            {
                "label": "Azure Costs",
                "icon": "fas fa-dollar-sign",
                "permission": "azure_costs.view_costs",
                "order": 2,
                "children": [
                    {
                        "label": "Current Month",
                        "url": "/costs/current",
                        "permission": "azure_costs.view_costs"
                    },
                    {
                        "label": "Cost History",
                        "url": "/costs/history",
                        "permission": "azure_costs.view_detailed_costs"
                    },
                    {
                        "label": "Cost Budgets",
                        "url": "/costs/budgets",
                        "permission": "azure_costs.manage_budgets"
                    }
                ]
            }
        ]
    }
```

#### azure_resources/resources/menu_manifest.py
```python
def get_menu_items():
    return {
        "service": "azure_resources",
        "items": [
            {
                "label": "Azure Resources",
                "icon": "fas fa-cloud",
                "permission": "azure_resources.view_resources",
                "order": 3,
                "children": [
                    {
                        "label": "All Resources",
                        "url": "/resources/",
                        "permission": "azure_resources.view_resources"
                    },
                    {
                        "label": "By Resource Group",
                        "url": "/resources/by-group",
                        "permission": "azure_resources.view_resources"
                    },
                    {
                        "label": "Resource Health",
                        "url": "/resources/health",
                        "permission": "azure_resources.view_resources"
                    },
                    {
                        "label": "Manage Resources",
                        "url": "/resources/manage",
                        "permission": "azure_resources.manage_resources"
                    }
                ]
            }
        ]
    }
```

### Menu Service Integration

The cielo_website needs to integrate with the menu service:

#### cielo_website/webapp/services/menu_service.py
```python
import requests
from django.core.cache import cache
from django.conf import settings

class MenuService:
    def __init__(self):
        self.identity_provider_url = settings.IDENTITY_PROVIDER_URL
        self.cache_key = 'menu_structure'
        self.cache_timeout = 300  # 5 minutes
    
    def get_menu_for_user(self, user_token):
        # Check cache first
        cache_key = f"{self.cache_key}:{user_token[:8]}"
        cached_menu = cache.get(cache_key)
        if cached_menu:
            return cached_menu
        
        # Fetch from identity provider
        headers = {'Authorization': f'Bearer {user_token}'}
        response = requests.get(
            f"{self.identity_provider_url}/api/menu/",
            headers=headers
        )
        
        if response.status_code == 200:
            menu_data = response.json()
            cache.set(cache_key, menu_data, self.cache_timeout)
            return menu_data
        
        return []
```

### Context Processor

Copy and adapt the menu context processor:

#### cielo_website/webapp/context_processors.py
```python
from .services.menu_service import MenuService

def menu_context(request):
    """Add menu items to template context"""
    menu_items = []
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        menu_service = MenuService()
        jwt_token = request.session.get('jwt_token')
        if jwt_token:
            menu_items = menu_service.get_menu_for_user(jwt_token)
    
    return {
        'menu_items': menu_items,
        'current_path': request.path
    }
```

### Template Integration

Use the menu in base template:

#### cielo_website/webapp/templates/base.html
```html
<nav class="sidebar">
    {% include 'components/menu.html' %}
</nav>
```

#### cielo_website/webapp/templates/components/menu.html
```html
<ul class="menu">
    {% for item in menu_items %}
        {% if item.children %}
            <li class="menu-item has-children {% if item.active %}active{% endif %}">
                <a href="#" class="menu-link" data-toggle="submenu">
                    <i class="{{ item.icon }}"></i>
                    <span>{{ item.label }}</span>
                    <i class="fas fa-chevron-down"></i>
                </a>
                <ul class="submenu">
                    {% for child in item.children %}
                        <li class="submenu-item {% if child.active %}active{% endif %}">
                            <a href="{{ child.url }}" class="submenu-link">
                                {{ child.label }}
                            </a>
                        </li>
                    {% endfor %}
                </ul>
            </li>
        {% else %}
            <li class="menu-item {% if item.active %}active{% endif %}">
                <a href="{{ item.url }}" class="menu-link">
                    <i class="{{ item.icon }}"></i>
                    <span>{{ item.label }}</span>
                </a>
            </li>
        {% endif %}
    {% endfor %}
</ul>
```

### Menu Cache Management

When permissions or menu items change, the cache must be invalidated:

```python
# In identity_provider when roles/permissions change
from django.core.cache import cache

def invalidate_user_menu_cache(user_id):
    # Clear specific user's menu cache
    pattern = f"menu_structure:*"
    cache.delete_pattern(pattern)
```

### Menu Features
1. **Dynamic Loading**: Menu items loaded based on user permissions
2. **Nested Menus**: Support for multi-level navigation
3. **Active State**: Automatic highlighting of current page
4. **Icon Support**: FontAwesome icons for visual hierarchy
5. **Order Control**: Menu items can be ordered explicitly
6. **Permission-Based**: Items only shown if user has required permission
7. **Service Discovery**: Each service registers its own menu items
8. **Cache Performance**: Redis caching for fast menu rendering

## Environment Variables

Add to `.env`:
```
# Cielo Project
CIELO_WEBSITE_SECRET_KEY=<generate-key>
AZURE_COSTS_SECRET_KEY=<generate-key>
AZURE_RESOURCES_SECRET_KEY=<generate-key>
```

## Test Users

### Demo User Configuration

Two additional test users will be created to demonstrate the domain-based access control:

#### Mary - Access to Current Services Only
```python
{
    "username": "mary",
    "email": "mary@example.com",
    "password": "MaryDemo123!",
    "roles": ["inventory_viewer", "billing_viewer"],
    "permissions": [
        # Can access vfservices.viloforge.com services
        "inventory.view_products",
        "billing.view_invoices",
        # NO cielo.access permission
    ],
    "access": {
        "vfservices.viloforge.com": True,
        "cielo.viloforge.com": False  # Will be redirected
    }
}
```

#### Paul - Access to Cielo Services Only
```python
{
    "username": "paul", 
    "email": "paul@example.com",
    "password": "PaulDemo123!",
    "roles": ["cielo_user"],
    "permissions": [
        "cielo.access",
        "azure_costs.view_costs",
        "azure_resources.view_resources",
        # NO inventory or billing permissions
    ],
    "access": {
        "vfservices.viloforge.com": True,  # Can login but won't see menu items
        "cielo.viloforge.com": True
    }
}
```

### Access Behavior

1. **Mary**:
   - Can login at identity.vfservices.viloforge.com
   - Can access vfservices.viloforge.com and see Inventory/Billing menus
   - If tries to access cielo.viloforge.com → redirected to viloforge.com
   
2. **Paul**:
   - Can login at identity.vfservices.viloforge.com
   - Can access vfservices.viloforge.com but sees empty/minimal menu
   - Can access cielo.viloforge.com and see Azure Costs/Resources menus

### Setup Command
```bash
# Add to identity-provider setup_demo_users command
python manage.py setup_demo_users --add-cielo-users
```

## Testing Strategy

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test API communication between services
3. **E2E Tests**: Test complete user flows through Playwright
4. **Permission Tests**: Verify RBAC/ABAC policies work correctly
5. **Cross-Domain Tests**: Verify Mary/Paul access restrictions

## Security Considerations

1. All services must validate JWT tokens
2. API services should not be directly accessible from outside
3. Use HTTPS for all external communication
4. Implement rate limiting on API endpoints
5. Log all authentication/authorization failures
6. Use environment variables for sensitive configuration

## Development Workflow

1. Develop each service independently
2. Use docker-compose for local testing
3. Test integration points thoroughly
4. Ensure all services handle identity-provider downtime gracefully
5. Implement proper error handling and logging

## Monitoring and Logging

1. Centralized logging to capture all service logs
2. Health check endpoints for each service
3. Metrics collection for API performance
4. Alert on authentication failures
5. Monitor resource usage per service