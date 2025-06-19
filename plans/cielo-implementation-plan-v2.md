# Cielo Implementation Plan v2 - Multi-Domain Architecture

## Overview
This revised plan corrects the domain architecture to properly support multiple independent application sets (VF Services and Cielo) sharing a single identity provider accessible through multiple URLs.

## Key Architecture Changes

### Terminology Update
- **OLD**: `BASE_DOMAIN` - Confusing when supporting multiple domains
- **NEW**: `APPLICATION_SET_DOMAIN` - Clear that each application set has its own domain

### Domain Structure
- **VF Services Domain**: `vfservices.viloforge.com`
  - Services: `www.`, `billing.`, `inventory.`, `identity.`
- **Cielo Domain**: `cielo.viloforge.com` 
  - Services: `www.`, `identity.`, `costs.`, `resources.`
- **Shared Parent**: `.viloforge.com` (for SSO cookies)

### Identity Provider Access
The identity provider is accessible at MULTIPLE URLs:
- `identity.vfservices.viloforge.com` (for VF Services users)
- `identity.cielo.viloforge.com` (for Cielo users)
- Future: `identity.<any-application-domain>`

## Implementation Status
- ✅ **Step 1**: Identity Provider Multi-Domain Support - PARTIALLY COMPLETE
  - ✓ CORS configuration for multiple domains
  - ✓ Redirect validation
  - ✗ Multi-URL access for identity provider (needs fixing)
  - ✗ APPLICATION_SET_DOMAIN implementation
- ⏳ **Step 2**: Fix Identity Provider for Multi-URL Access - NOT STARTED
- ⏳ **Step 3**: Create Cielo Website with Correct Domain - NOT STARTED  
- ⏳ **Step 4**: Add Test Users (Mary & Paul) - NOT STARTED
- ⏳ **Step 5**: Implement Menu System for Cielo - NOT STARTED
- ⏳ **Step 6**: Create Azure Costs API Service - NOT STARTED
- ⏳ **Step 7**: Create Azure Resources API Service - NOT STARTED
- ⏳ **Step 8**: Integrate APIs with Cielo Website - NOT STARTED
- ⏳ **Step 9**: Polish and Complete Demo - NOT STARTED

---

## Step 1: Identity Provider Multi-Domain Support (NEEDS FIXES)

### What Was Done ✅
- Added CORS support for multiple domains
- Implemented redirect URL validation
- Created test scripts

### What Needs Fixing ❌
1. Identity provider only accessible at `identity.vfservices.viloforge.com`
2. Need to add routing for `identity.cielo.viloforge.com`
3. Need to implement APPLICATION_SET_DOMAIN concept
4. Need dynamic domain detection in identity provider

---

## Step 2: Fix Identity Provider for Multi-URL Access
**Goal**: Enable identity provider to be accessed from multiple domains

### Tasks:
1. Update docker-compose.yml with multiple Traefik routes
2. Implement APPLICATION_SET_DOMAIN environment variable
3. Update identity provider to detect which domain it's accessed from
4. Update CORS to dynamically build allowed origins
5. Update redirect validation to handle multiple domains
6. Test access from both identity URLs

### Docker Compose Changes:
```yaml
identity-provider:
  environment:
    - ALLOWED_APPLICATION_DOMAINS=vfservices.viloforge.com,cielo.viloforge.com
    - SSO_COOKIE_DOMAIN=.viloforge.com
  labels:
    - "traefik.enable=true"
    # Multiple routes to same service
    - "traefik.http.routers.identity-vf.rule=Host(`identity.vfservices.viloforge.com`)"
    - "traefik.http.routers.identity-cielo.rule=Host(`identity.cielo.viloforge.com`)"
    - "traefik.http.routers.identity-vf.entrypoints=websecure"
    - "traefik.http.routers.identity-cielo.entrypoints=websecure"
    - "traefik.http.routers.identity-vf.tls=true"
    - "traefik.http.routers.identity-cielo.tls=true"
    - "traefik.http.routers.identity-vf.service=identity-service"
    - "traefik.http.routers.identity-cielo.service=identity-service"
    - "traefik.http.services.identity-service.loadbalancer.server.port=8000"
```

### Identity Provider Code Changes:
```python
# identity_app/views.py
def get_application_domain(request):
    """Detect which application domain is accessing identity service"""
    host = request.get_host()
    if host.startswith('identity.'):
        return host[9:]  # Remove 'identity.' prefix
    return settings.ALLOWED_APPLICATION_DOMAINS[0]
```

### Success Criteria:
- Can access login at `identity.vfservices.viloforge.com`
- Can access login at `identity.cielo.viloforge.com`
- Both URLs serve the same identity provider
- Redirects work correctly for each domain

---

## Step 3: Create Cielo Website with Correct Domain
**Goal**: Create Cielo website at cielo.viloforge.com (NOT a subdomain of vfservices)

### Tasks:
1. Create cielo_website Django project
2. Configure with APPLICATION_SET_DOMAIN=cielo.viloforge.com
3. Set identity provider URL to identity.cielo.viloforge.com
4. Implement CieloAccessMiddleware
5. Configure Traefik for cielo.viloforge.com
6. Test domain isolation

### Docker Compose Configuration:
```yaml
cielo-website:
  build:
    context: .
    dockerfile: cielo_website/Dockerfile
  environment:
    - APPLICATION_SET_DOMAIN=cielo.viloforge.com
    - IDENTITY_PROVIDER_URL=https://identity.cielo.viloforge.com
    - SSO_COOKIE_DOMAIN=.viloforge.com
    - VF_JWT_SECRET=${VF_JWT_SECRET:-change-me}
  labels:
    - "traefik.enable=true"
    - "traefik.http.routers.cielo-website.rule=Host(`cielo.viloforge.com`)"
    - "traefik.http.routers.cielo-website.entrypoints=websecure"
    - "traefik.http.routers.cielo-website.tls=true"
    - "traefik.http.services.cielo-website.loadbalancer.server.port=8000"
```

### Key Differences from Current Implementation:
1. **Domain**: `cielo.viloforge.com` NOT `cielo.vfservices.viloforge.com`
2. **Identity URL**: Points to `identity.cielo.viloforge.com`
3. **Environment**: Uses APPLICATION_SET_DOMAIN instead of BASE_DOMAIN

### Success Criteria:
- cielo.viloforge.com is accessible
- Login redirects to identity.cielo.viloforge.com
- SSO works between vfservices and cielo domains
- Users without cielo.access permission are redirected

---

## Step 4: Add Test Users (Mary & Paul)
**Goal**: Demonstrate domain-based access control

### Test Users:
1. **Mary**: Access to vfservices.viloforge.com only
   - Roles: inventory_viewer, billing_viewer
   - NO cielo.access permission
   
2. **Paul**: Access to cielo.viloforge.com only
   - Roles: cielo_user
   - Has cielo.access permission
   - NO inventory/billing permissions

### Demo Scenarios:
1. Mary logs in at identity.vfservices.viloforge.com
   - Can access vfservices.viloforge.com ✓
   - Redirected from cielo.viloforge.com ✗

2. Paul logs in at identity.cielo.viloforge.com
   - Can access cielo.viloforge.com ✓
   - Sees empty menu on vfservices.viloforge.com

### Success Criteria:
- Domain-based access control works
- Same user database across domains
- Permissions determine access

---

## Step 5: Implement Menu System for Cielo
**Goal**: Dynamic menu showing only permitted items

### Tasks:
1. Create menu service integration in cielo_website
2. Register Cielo menu items with permissions
3. Configure menu aggregation from Cielo services
4. Test menu filtering based on permissions

### Menu Configuration:
- Menu items fetched from identity.cielo.viloforge.com
- Filtered based on user's permissions
- Cached in Redis for performance

### Success Criteria:
- Paul sees Cielo-specific menu items
- Mary sees no menu items on Cielo
- Menu updates when permissions change

---

## Step 6: Create Azure Costs API Service
**Goal**: Internal API service for Azure cost data

### Configuration:
```yaml
azure-costs:
  environment:
    - APPLICATION_SET_DOMAIN=cielo.viloforge.com
    - SERVICE_SUBDOMAIN=costs  # Makes costs.cielo.viloforge.com
```

### Endpoints:
- `/api/costs/current`
- `/api/costs/history`
- `/api/costs/forecast`

### Success Criteria:
- API accessible internally
- Requires JWT authentication
- Permissions enforced

---

## Step 7: Create Azure Resources API Service
**Goal**: Internal API service for Azure resources

### Configuration:
```yaml
azure-resources:
  environment:
    - APPLICATION_SET_DOMAIN=cielo.viloforge.com
    - SERVICE_SUBDOMAIN=resources
```

### Endpoints:
- `/api/resources/list`
- `/api/resources/health`
- `/api/resources/{id}`

### Success Criteria:
- API returns mock data
- Authentication required
- Integrates with menu system

---

## Step 8: Integrate APIs with Cielo Website
**Goal**: Display data from API services

### Tasks:
1. Create service clients in cielo_website
2. Build dashboard with API data
3. Implement error handling
4. Add loading states

### Success Criteria:
- Dashboard shows cost and resource data
- Handles API failures gracefully
- Performance is acceptable

---

## Step 9: Polish and Complete Demo
**Goal**: Professional demo showcasing multi-domain architecture

### Tasks:
1. Add Cielo branding/styling
2. Create realistic mock data
3. Build demo script
4. Test all user scenarios

### Demo Flow:
1. Show VF Services domain with existing users
2. Show Cielo domain with different branding
3. Demonstrate Mary's access (VF only)
4. Demonstrate Paul's access (Cielo only)
5. Show shared identity provider
6. Demonstrate permission-based menus

---

## Technical Implementation Details

### Environment Variable Updates
Replace all instances of `BASE_DOMAIN` with `APPLICATION_SET_DOMAIN`:

```yaml
# Old
- BASE_DOMAIN=vfservices.viloforge.com

# New - VF Services
- APPLICATION_SET_DOMAIN=vfservices.viloforge.com

# New - Cielo
- APPLICATION_SET_DOMAIN=cielo.viloforge.com
```

### Identity Provider Updates
```python
# settings.py
ALLOWED_APPLICATION_DOMAINS = os.environ.get(
    'ALLOWED_APPLICATION_DOMAINS', 
    'vfservices.viloforge.com'
).split(',')

# Build CORS dynamically
CORS_ALLOWED_ORIGINS = []
for domain in ALLOWED_APPLICATION_DOMAINS:
    CORS_ALLOWED_ORIGINS.extend([
        f"https://{domain}",
        f"https://www.{domain}",
        f"https://identity.{domain}",
    ])
```

### Service Configuration Pattern
Each service should:
1. Use APPLICATION_SET_DOMAIN for its domain
2. Construct identity URL as `identity.{APPLICATION_SET_DOMAIN}`
3. Use consistent SERVICE_SUBDOMAIN if applicable

### DNS Requirements
- `cielo.viloforge.com` → Server IP
- `identity.cielo.viloforge.com` → Server IP  
- `*.cielo.viloforge.com` → Server IP (for future services)

### SSL Certificate
The existing wildcard certificate for `*.viloforge.com` covers:
- `*.vfservices.viloforge.com`
- `*.cielo.viloforge.com`
- Any future `*.<app>.viloforge.com`

---

## Timeline Estimate

- Step 2: 2-3 hours (Fix identity provider)
- Step 3: 2-3 hours (Create Cielo website correctly)
- Step 4: 1 hour (Test users)
- Step 5: 2 hours (Menu system)
- Step 6: 2-3 hours (Azure costs API)
- Step 7: 2-3 hours (Azure resources API)
- Step 8: 3-4 hours (Integration)
- Step 9: 2-3 hours (Polish)

**Total: 16-22 hours**

---

## Key Differences from Original Plan

1. **Multiple Identity URLs**: Identity provider accessible at multiple domains
2. **Separate Domains**: Cielo is cielo.viloforge.com, not cielo.vfservices.viloforge.com
3. **APPLICATION_SET_DOMAIN**: Clear terminology for domain sets
4. **Dynamic Configuration**: Services detect their domain context
5. **Scalable Architecture**: Easy to add new application domains

---

## Success Metrics

1. Two independent domains sharing one user base
2. Identity provider accessible from both domains
3. Permission-based access control across domains
4. Clean separation of application sets
5. Foundation for future multi-tenant expansion