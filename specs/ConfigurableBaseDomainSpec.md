# Configurable Base Domain Specification

## Executive Summary

This specification outlines the plan to make the VF Services platform domain configurable through environment variables, allowing easy deployment to different domains without code changes.

## Current State

The platform consists of 4 Django projects using `vfservices.viloforge.com` as the base domain:
- **Identity Provider**: `identity.vfservices.viloforge.com` (Authentication & identity management)
- **Website**: `vfservices.viloforge.com` or `website.vfservices.viloforge.com` (Main web application)
- **Billing API**: `billing.vfservices.viloforge.com` (Billing and payment processing)
- **Inventory API**: `inventory.vfservices.viloforge.com` (Inventory management)

## Problem Analysis

### 1. Partial Implementation

#### Django Settings Status:
- ✅ **identity-provider**: Fully configured with `BASE_DOMAIN` in settings.py
- ✅ **website**: Fully configured with `BASE_DOMAIN` in settings.py
- ❌ **billing-api**: Missing `BASE_DOMAIN` configuration in settings.py
- ❌ **inventory-api**: Missing `BASE_DOMAIN` configuration in settings.py

#### Docker Compose Status:
- ✅ **identity-provider**: Has `BASE_DOMAIN` environment variable
- ✅ **website**: Has `BASE_DOMAIN` environment variable
- ❌ **billing-api**: Missing `BASE_DOMAIN` environment variable
- ❌ **inventory-api**: Missing `BASE_DOMAIN` environment variable
- ✅ All services have `SSO_COOKIE_DOMAIN` using `BASE_DOMAIN`
- ✅ All Traefik routing rules use `BASE_DOMAIN`

#### Other Components:
- ✅ Shell scripts in `/scripts/` use `BASE_DOMAIN`

### 2. Hardcoded References

Comprehensive search reveals hardcoded `vfservices.viloforge.com` references across all Django projects:

#### Identity Provider
- **main/settings.py**:
  - Line 206: `'DEFAULT_HOST': 'identity.vfservices.viloforge.com'` (Swagger settings)
  - Lines 219-224: Hardcoded CORS_ALLOWED_ORIGINS list
- **main/urls.py**:
  - Line 32: `terms_of_service="https://www.vfservices.viloforge.com/terms/"`
  - Line 38: `url='https://identity.vfservices.viloforge.com/'` (Swagger schema)
- **identity_app/cors_discovery.py**:
  - Lines 54-56, 70: Safe domains list (may be intentionally hardcoded for security)

#### Website
- **webapp/templates/webapp/index.html** (Lines 20-23):
  ```html
  <a href="https://identity.vfservices.viloforge.com">Identity Provider</a>
  <a href="https://website.vfservices.viloforge.com">Website</a>
  <a href="https://billing.vfservices.viloforge.com">Billing API</a>
  <a href="https://inventory.vfservices.viloforge.com">Inventory API</a>
  ```
- **webapp/templates/webapp/private.html** (Line 268):
  ```html
  <a href="https://identity.vfservices.viloforge.com/admin/">Identity Admin</a>
  ```

#### Billing API
- **main/settings.py**:
  - Line 33: `ALLOWED_HOSTS = ["billing.vfservices.viloforge.com", ...]`
  - Line 310: `CORS_ALLOWED_ORIGINS = ["https://website.vfservices.viloforge.com", ...]`

#### Inventory API
- **main/settings.py**:
  - Line 33: `ALLOWED_HOSTS = ["inventory.vfservices.viloforge.com", ...]`
  - Line 310: `CORS_ALLOWED_ORIGINS = ["https://website.vfservices.viloforge.com", ...]`

#### Other Configuration Files
- **traefik/dynamic/tls-config.yaml**: Certificate paths reference `vfservices.viloforge.com`

### 3. Test Files

Extensive hardcoded domain usage found across the test suite:

#### Test Configuration
- **tests/.env** (Lines 10-13): All service URLs hardcoded
  ```bash
  IDENTITY_URL=https://identity.vfservices.viloforge.com
  WEBSITE_URL=https://website.vfservices.viloforge.com
  BILLING_URL=https://billing.vfservices.viloforge.com
  INVENTORY_URL=https://inventory.vfservices.viloforge.com
  ```
- **tests/e2e/playwright.config.py** (Line 9): Default BASE_URL

#### Integration Tests (Root Level)
Multiple test files with hardcoded service URLs:
- `test_alice_traefik.py`, `test_playground_scenarios.py`: All service URLs
- `test_dashboard_menu.py`, `test_menu_*.py`: Website URLs
- Various debug scripts: `debug_menu_api.py`, `check_dashboard_html.py`

#### E2E Tests
- **tests/e2e/test_rbac_demo_alice.py**: Uses BASE_URL from environment

#### Key Patterns
1. Most tests hardcode service URLs directly in the file
2. Some tests read from `tests/.env` but that file has hardcoded URLs
3. No tests currently use dynamic domain configuration

## Proposed Solution

### 1. Environment Variable Strategy

Create a single `BASE_DOMAIN` environment variable that propagates throughout the system:

```bash
BASE_DOMAIN=example.com  # Changes all services to use example.com
```

### 2. Implementation Plan

#### Phase 1: Update Docker Compose Configuration

The `docker-compose.yml` file already uses `BASE_DOMAIN` in most places, but needs minor updates:

**Current State:**
- Traefik labels use `${BASE_DOMAIN:-vfservices.viloforge.com}` for routing rules
- `identity-provider` and `website` services have `BASE_DOMAIN` environment variable
- `billing-api` and `inventory-api` services are **missing** `BASE_DOMAIN` environment variable

**Required Change:**
Add `BASE_DOMAIN` environment variable to `billing-api` and `inventory-api` services:

```yaml
billing-api:
  environment:
    - BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
    # ... other environment variables

inventory-api:
  environment:
    - BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
    # ... other environment variables
```

#### Phase 2: Update Django Settings

**billing-api/main/settings.py**:
```python
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "vfservices.viloforge.com")

ALLOWED_HOSTS = [
    f"billing.{BASE_DOMAIN}",
    f".{BASE_DOMAIN}",
    "localhost",
    "127.0.0.1",
    "billing-api",
]

CORS_ALLOWED_ORIGINS = [
    f"https://website.{BASE_DOMAIN}",
    f"https://{BASE_DOMAIN}",
    "http://localhost:8080",
]
```

**inventory-api/main/settings.py**:
```python
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "vfservices.viloforge.com")

ALLOWED_HOSTS = [
    f"inventory.{BASE_DOMAIN}",
    f".{BASE_DOMAIN}",
    "localhost",
    "127.0.0.1",
    "inventory-api",
]

CORS_ALLOWED_ORIGINS = [
    f"https://website.{BASE_DOMAIN}",
    f"https://{BASE_DOMAIN}",
    "http://localhost:8080",
]
```

#### Phase 3: Update Templates

Create a context processor to inject service URLs:

**website/webapp/context_processors.py**:
```python
from django.conf import settings

def service_urls(request):
    base_domain = settings.BASE_DOMAIN
    return {
        'SERVICE_URLS': {
            'identity': f'https://identity.{base_domain}',
            'website': f'https://website.{base_domain}',
            'billing': f'https://billing.{base_domain}',
            'inventory': f'https://inventory.{base_domain}',
        }
    }
```

Update templates to use context variables:
```html
<a href="{{ SERVICE_URLS.identity }}">Identity Provider</a>
```

#### Phase 4: Dynamic Traefik Configuration

Update **traefik/dynamic/tls-config.yaml** to support multiple domains:

```yaml
tls:
  certificates:
    - certFile: /etc/certs/live/${BASE_DOMAIN}/fullchain.pem
      keyFile: /etc/certs/live/${BASE_DOMAIN}/privkey.pem
```

This requires updating the Traefik container to support environment variable substitution or generating the config dynamically.

#### Phase 5: Certificate Management

Update certificate scripts to use `BASE_DOMAIN`:
- Modify `scripts/generate_certs.sh` to generate wildcard certificates for `*.${BASE_DOMAIN}`
- Update certificate paths in Docker volumes

#### Phase 6: Test Configuration

##### Update Test Environment Files
Create **tests/.env.template**:
```bash
# Service URLs using BASE_DOMAIN
BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
IDENTITY_URL=https://identity.${BASE_DOMAIN}
WEBSITE_URL=https://website.${BASE_DOMAIN}
BILLING_URL=https://billing.${BASE_DOMAIN}
INVENTORY_URL=https://inventory.${BASE_DOMAIN}
BASE_URL=https://${BASE_DOMAIN}

# Other test configuration
NODE_ENV=test
TEST_ENV=development
PWDEBUG=0
```

##### Create Test Configuration Script
**scripts/generate_test_env.sh**:
```bash
#!/bin/bash
BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
envsubst < tests/.env.template > tests/.env
```

##### Update Test Files Strategy
1. Create a base test configuration module that reads from environment
2. Update individual test files to import service URLs from the config module
3. For CI/CD, set BASE_DOMAIN before running tests

### 3. Configuration Management

#### Option 1: Single .env File (Recommended)
Create a root `.env` file:
```bash
BASE_DOMAIN=example.com
```

Docker Compose will automatically load this, and we can source it in shell scripts.

#### Option 2: Multiple Environment Files
- `.env.production`: `BASE_DOMAIN=vfservices.viloforge.com`
- `.env.staging`: `BASE_DOMAIN=staging.example.com`
- `.env.development`: `BASE_DOMAIN=dev.local`

### 4. Deployment Process

1. Set `BASE_DOMAIN` in environment or `.env` file
2. Generate/obtain SSL certificates for the new domain
3. Run `docker-compose up` - all services will use the new domain
4. No code changes required!

### 5. Backward Compatibility

Default values ensure the system works without configuration:
- If `BASE_DOMAIN` is not set, it defaults to `vfservices.viloforge.com`
- Existing deployments continue to work unchanged

## Implementation Checklist

### Docker Compose Updates
- [ ] Add `BASE_DOMAIN` environment variable to `billing-api` service
- [ ] Add `BASE_DOMAIN` environment variable to `inventory-api` service

### Identity Provider Updates
- [ ] Update `main/settings.py` SWAGGER_SETTINGS to use BASE_DOMAIN
- [ ] Update `main/settings.py` CORS_ALLOWED_ORIGINS to use BASE_DOMAIN
- [ ] Update `main/urls.py` terms_of_service URL to use BASE_DOMAIN
- [ ] Update `main/urls.py` swagger schema URL to use BASE_DOMAIN
- [ ] Review `identity_app/cors_discovery.py` safe domains list (security consideration)

### Website Updates
- [ ] Create context processor for service URLs
- [ ] Add context processor to `website/main/settings.py`
- [ ] Update `webapp/templates/webapp/index.html` to use context variables (4 service links)
- [ ] Update `webapp/templates/webapp/private.html` to use context variables (identity admin link)

### Billing API Updates
- [ ] Add BASE_DOMAIN to `main/settings.py`
- [ ] Update ALLOWED_HOSTS to use BASE_DOMAIN
- [ ] Update CORS_ALLOWED_ORIGINS to use BASE_DOMAIN

### Inventory API Updates
- [ ] Add BASE_DOMAIN to `main/settings.py`
- [ ] Update ALLOWED_HOSTS to use BASE_DOMAIN
- [ ] Update CORS_ALLOWED_ORIGINS to use BASE_DOMAIN

### Infrastructure Updates
- [ ] Create dynamic Traefik configuration solution
- [ ] Update certificate generation scripts
- [ ] Update documentation

### Test Suite Updates
- [ ] Create `tests/.env.template` with BASE_DOMAIN variables
- [ ] Create `scripts/generate_test_env.sh` script
- [ ] Update `tests/e2e/playwright.config.py` to use BASE_DOMAIN
- [ ] Create test configuration module for shared URL configuration
- [ ] Update root-level test files to use configuration module:
  - [ ] `test_alice_traefik.py`
  - [ ] `test_playground_scenarios.py`
  - [ ] `test_dashboard_menu.py`
  - [ ] All `test_menu_*.py` files
- [ ] Update debug scripts to use dynamic URLs
- [ ] Document test configuration in README

### Testing
- [ ] Test with different domains (e.g., `local.test`, `staging.example.com`)
- [ ] Verify CORS works correctly across all services
- [ ] Test authentication flow with new domain
- [ ] Verify SSL certificates work properly
- [ ] Run full test suite with custom domain
- [ ] Test CI/CD pipeline with BASE_DOMAIN override

## Testing Strategy

1. **Local Testing**: Use `BASE_DOMAIN=local.test` with self-signed certificates
2. **Staging**: Deploy to a staging domain to verify all services work
3. **Production Migration**: Update `BASE_DOMAIN` and redeploy

## Security Considerations

1. Ensure CORS settings are properly updated for the new domain
2. SSL certificates must be valid for the new domain
3. Update any external service webhooks or OAuth callbacks
4. Review and update any hardcoded URLs in external configurations

## Risks and Mitigation

1. **Risk**: Missed hardcoded references
   - **Mitigation**: Comprehensive grep search before deployment
   
2. **Risk**: Certificate issues
   - **Mitigation**: Test certificate generation process thoroughly
   
3. **Risk**: External service integration failures
   - **Mitigation**: Document all external dependencies that need updating

## Conclusion

This approach provides a clean, maintainable solution for domain configuration while maintaining backward compatibility and requiring minimal changes to the existing codebase.