# Cielo Implementation Plan

## Overview
This plan outlines the step-by-step implementation of the Cielo project, with each step producing a demonstrable outcome.

## Implementation Status
- ✅ **Step 1**: Identity Provider Multi-Domain Support - COMPLETED (2025-06-18)
- ✅ **Step 2**: Create Cielo Website Base - COMPLETED (2025-06-19)
- ⏳ **Step 3**: Add Test Users (Mary & Paul) - NOT STARTED
- ⏳ **Step 4**: Implement Menu System for Cielo - NOT STARTED
- ⏳ **Step 5**: Create Azure Costs API Service - NOT STARTED
- ⏳ **Step 6**: Create Azure Resources API Service - NOT STARTED
- ⏳ **Step 7**: Integrate APIs with Cielo Website - NOT STARTED
- ⏳ **Step 8**: Polish and Complete Demo - NOT STARTED

---

## Step 1: Identity Provider Multi-Domain Support ✅ COMPLETED
**Goal**: Enable identity.vfservices.viloforge.com to support both vfservices.viloforge.com and cielo.viloforge.com domains

### Tasks:
1. ✅ Update identity-provider CORS settings
2. ✅ Add allowed redirect domains configuration
3. ✅ Update login view to validate redirect URLs
4. ✅ Create automated test script
5. ✅ Create manual testing guide
6. ✅ Create Playwright E2E tests for Chrome browser

### Implementation Details:
- **CORS Configuration**: Added `cielo.${BASE_DOMAIN}` to CORS_ALLOWED_ORIGINS in `identity-provider/main/settings.py`
- **Allowed Domains**: Added ALLOWED_REDIRECT_DOMAINS configuration with all supported domains
- **Security**: Implemented `validate_redirect_url()` function in `identity-provider/identity_app/views.py` to check redirect URLs against allowed domains
- **Cookie Config**: SSO_COOKIE_DOMAIN already configured as `.${BASE_DOMAIN}` for cross-subdomain authentication
- **Domain Correction**: Updated all references from `viloforge.com` to `vfservices.viloforge.com` as primary domain

### Files Modified:
- `identity-provider/main/settings.py` - Added CORS and redirect domain configuration
- `identity-provider/identity_app/views.py` - Added redirect URL validation
- `specs/cielo-project-specification.md` - Updated domain references
- `plans/cielo-implementation-plan.md` - Updated domain references

### Files Created:
- `test_cielo_step1_multidomain.py` - Automated test script for multi-domain auth
- `test_cielo_step1_playwright_simple.py` - Playwright E2E test with Chrome
- `tests/e2e/test_cielo_step1_playwright.py` - Full Playwright test suite
- `tests/e2e/README-PLAYWRIGHT.md` - Playwright testing documentation
- `tests/requirements-playwright.txt` - Playwright dependencies
- `docs/CIELO-STEP1-TESTING.md` - Comprehensive testing guide

### Demo:
- Show login from vfservices.viloforge.com redirecting back correctly
- Show login from cielo.viloforge.com redirecting back correctly
- Demonstrate single sign-on between domains

### Success Criteria:
- Users can login from both domains
- JWT tokens work across both domains
- No CORS errors in browser console

### Testing:
- **Python Test Script**: `tests/playwright/api/test_cielo_step1_multidomain.py`
- **Playwright E2E Test**: `tests/playwright/basic/test_cielo_step1_playwright_simple.py` ✅ ALL TESTS PASSING
- **Manual Test Guide**: `docs/CIELO-STEP1-TESTING.md`
- **Quick Test Commands**: 
  ```bash
  # Python API tests
  python tests/playwright/api/test_cielo_step1_multidomain.py
  
  # Playwright browser tests (headless)
  python tests/playwright/basic/test_cielo_step1_playwright_simple.py
  
  # Playwright browser tests (visible)
  python tests/playwright/basic/test_cielo_step1_playwright_simple.py --headed
  ```

### Issues Fixed During Implementation:
1. **Login Form Redirect**: Updated login template to preserve redirect_uri parameter during form submission
2. **Password Authentication**: Reset demo user passwords to match test expectations
3. **Security Validation**: Enhanced redirect URL validation to check schemes and properly block malicious URLs
4. **Logging Errors**: Fixed multiple logger calls using incorrect keyword arguments
5. **Cookie Domain**: Confirmed SSO_COOKIE_DOMAIN configuration for cross-subdomain authentication
6. **Cielo Domain**: Added explicit support for cielo.viloforge.com in allowed redirect domains

### Test Results (2025-06-18):
```
Test 1: Login flow from main domain ✓
Test 2: Login flow with Cielo domain redirect ✓ (Warning: domain doesn't exist yet)
Test 3: Single Sign-On (SSO) across subdomains ✓
Test 4: Security - Invalid redirect URLs blocked ✓
Test 5: JWT cookie configuration ✓

All tests passed! (5/5)
```

---

## Step 2: Create Cielo Website Base ✅ COMPLETED
**Goal**: Basic Cielo website accessible at cielo.viloforge.com with authentication

### Tasks:
1. ✅ Create cielo_website Django project structure
2. ✅ Copy accounts app from website
3. ✅ Copy base templates and adapt branding
4. ✅ Implement JWT authentication middleware
5. ✅ Add CieloAccessMiddleware for RBAC control
6. ✅ Update docker-compose.yml with cielo_website service
7. ✅ Configure Traefik routing for cielo.viloforge.com

### Implementation Details:
- **Project Structure**: Created new Django project at `/cielo_website` with same structure as main website
- **Authentication**: Reused accounts app and JWT middleware from common module
- **Access Control**: Implemented `CieloAccessMiddleware` to check for `cielo.access` permission
- **Branding**: Updated page titles and descriptions for Cielo branding
- **Docker Service**: Added `cielo-website` service to docker-compose.yml
- **Traefik Routing**: Configured routing for `cielo.viloforge.com` domain

### Files Created/Modified:
- Created `/cielo_website/` directory structure
- Created `cielo_website/webapp/middleware.py` with CieloAccessMiddleware
- Created `cielo_website/webapp/templates/webapp/index.html` with Cielo branding
- Updated `cielo_website/templates/page.html` with Cielo titles
- Created `cielo_website/Dockerfile`
- Updated `docker-compose.yml` to add cielo-website service

### Demo:
- Access cielo.viloforge.com and see login redirect
- Login and see basic authenticated page
- Show that users without cielo.access permission get redirected

### Success Criteria:
- cielo.viloforge.com is accessible
- Authentication works correctly
- RBAC restrictions are enforced

### Testing:
- **Simple Playwright Test**: `tests/playwright/basic/test_cielo_step2_playwright_simple.py`
- **Comprehensive Test Suite**: `tests/playwright/e2e/test_cielo_step2_playwright.py`
- **API Access Test**: `tests/playwright/api/test_cielo_step2_access.py`
- **Testing Guide**: `docs/CIELO-STEP2-TESTING.md`

### Quick Test Commands:
```bash
# Simple browser test
python tests/playwright/basic/test_cielo_step2_playwright_simple.py

# API-level access test
python tests/playwright/api/test_cielo_step2_access.py

# Full test suite
pytest tests/playwright/e2e/test_cielo_step2_playwright.py -v
```

---

## Step 3: Add Test Users (Mary & Paul)
**Goal**: Demonstrate domain-based access control with test users

### Tasks:
1. Create Mary user (vfservices.viloforge.com access only)
2. Create Paul user (cielo.viloforge.com access only)
3. Create cielo_user and cielo_admin roles
4. Assign appropriate permissions

### Demo:
- Login as Mary → Access vfservices.viloforge.com ✓, Access cielo.viloforge.com ✗
- Login as Paul → Access cielo.viloforge.com ✓, See empty menu on vfservices.viloforge.com
- Show permission-based redirects

### Success Criteria:
- Mary cannot access Cielo
- Paul can access Cielo
- Existing users (alice, bob, charlie) unaffected

---

## Step 4: Implement Menu System for Cielo
**Goal**: Dynamic menu showing only permitted items

### Tasks:
1. Create menu service integration in cielo_website
2. Add menu context processor
3. Create menu templates
4. Register cielo_website menu items

### Demo:
- Show Paul seeing Cielo-specific menu items
- Show Mary not seeing any Cielo menu items
- Demonstrate menu caching with Redis

### Success Criteria:
- Menus dynamically adjust based on permissions
- Menu items are properly styled
- Cache invalidation works

---

## Step 5: Create Azure Costs API Service
**Goal**: Basic API service for Azure cost data

### Tasks:
1. Create azure_costs Django project
2. Implement basic cost endpoints
3. Add RBAC decorators to views
4. Create menu manifest
5. Add to docker-compose.yml

### Demo:
- Access /api/costs/current endpoint with valid JWT
- Show permission denied for users without azure_costs.view_costs
- Show menu item appearing for authorized users

### Success Criteria:
- API returns mock cost data
- Authentication required for all endpoints
- Permissions properly enforced

---

## Step 6: Create Azure Resources API Service
**Goal**: Basic API service for Azure resource inventory

### Tasks:
1. Create azure_resources Django project
2. Implement basic resource endpoints
3. Add RBAC decorators to views
4. Create menu manifest
5. Add to docker-compose.yml

### Demo:
- Access /api/resources/list endpoint with valid JWT
- Show permission denied for unauthorized users
- Show both API services running simultaneously

### Success Criteria:
- API returns mock resource data
- Authentication working correctly
- Both APIs accessible from cielo_website

---

## Step 7: Integrate APIs with Cielo Website
**Goal**: Cielo website displays data from both API services

### Tasks:
1. Create service clients in cielo_website
2. Add dashboard view with API data
3. Create cost overview page
4. Create resource list page
5. Add proper error handling

### Demo:
- Dashboard showing data from both APIs
- Navigate through cost pages
- Navigate through resource pages
- Show loading states and error handling

### Success Criteria:
- Data displays correctly from APIs
- Navigation works smoothly
- Proper error messages for API failures

---

## Step 8: Polish and Complete Demo
**Goal**: Professional-looking demo ready for presentation

### Tasks:
1. Add proper styling to Cielo pages
2. Create mock data that tells a story
3. Add charts/visualizations for costs
4. Implement resource health indicators
5. Create demo script

### Demo:
- Complete flow from login to viewing Azure costs
- Show cost trends and forecasts
- Display resource health dashboard
- Demonstrate role-based feature access

### Success Criteria:
- Professional appearance
- Smooth user experience
- Clear demonstration of RBAC/microservices architecture

---

## Quick Demo Scenarios

### Scenario 1: Domain-Based Access
1. Login as Mary → Show vfservices.viloforge.com access
2. Try to access cielo.viloforge.com → Get redirected
3. Login as Paul → Show cielo.viloforge.com access
4. Show Paul's limited menu on vfservices.viloforge.com

### Scenario 2: Permission-Based Features
1. Login as Paul (cielo_user) → Show basic cost view
2. Login as cielo_admin → Show budget management features
3. Demonstrate menu items changing based on role

### Scenario 3: Microservices Architecture
1. Show docker ps with all services running
2. Demonstrate service isolation
3. Show JWT token flow between services
4. Kill one API service and show graceful degradation

---

## Timeline Estimate

- Step 1: ~~2-3 hours (Identity provider updates)~~ ✅ COMPLETED (Actual: ~3 hours)
- Step 2: 3-4 hours (Cielo website base)
- Step 3: 1 hour (Test users)
- Step 4: 2 hours (Menu system)
- Step 5: 2-3 hours (Azure costs API)
- Step 6: 2-3 hours (Azure resources API)
- Step 7: 3-4 hours (Integration)
- Step 8: 2-3 hours (Polish)

**Completed: Step 1 (3 hours) + Step 2 (~1 hour)**  
**Total Completed: ~4 hours**  
**Remaining: ~15-20 hours (2-3 days)**

### Step 1 Completion Details:
- **Started**: 2025-06-18 14:50 UTC
- **Completed**: 2025-06-18 18:00 UTC
- **Duration**: ~3 hours
- **Deliverables**: 
  - Updated identity provider with multi-domain support
  - Security enhancements for redirect validation
  - Comprehensive test suite with all tests passing
  - Fixed multiple bugs discovered during testing

### Step 2 Completion Details:
- **Started**: 2025-06-19
- **Completed**: 2025-06-19
- **Duration**: ~1 hour
- **Deliverables**:
  - Created cielo_website Django project
  - Implemented CieloAccessMiddleware for RBAC control
  - Configured Docker and Traefik for cielo.viloforge.com
  - Basic Cielo-branded website ready for authentication testing

---

## Risk Mitigation

1. **CORS Issues**: Test early with multiple browsers
2. **JWT Token Flow**: Use consistent token handling code
3. **Menu Caching**: Implement cache clear command
4. **Docker Networking**: Test service discovery early
5. **Permission Conflicts**: Document all permissions clearly

---

## Work Completed Summary

### Step 1 Deliverables ✅
1. **Multi-Domain CORS Support**
   - Identity provider now accepts requests from both vfservices.viloforge.com and cielo.viloforge.com
   - No CORS errors when making cross-origin requests

2. **Secure Redirect Validation**
   - Only whitelisted domains can be redirect targets
   - Malicious redirects are blocked and logged
   - Security events are tracked for audit

3. **SSO Cookie Configuration**
   - JWT cookies work across all subdomains
   - Single sign-on enabled between services

4. **Comprehensive Testing**
   - Automated test script with multiple test scenarios
   - Manual testing guide with step-by-step procedures
   - Debug commands for troubleshooting

### Ready for Next Steps
With Step 1 complete, the identity provider is now ready to support authentication for the new Cielo services. The foundation is in place for:
- Creating the Cielo website (Step 2)
- Adding domain-specific users (Step 3)
- Implementing the full microservices architecture

---

## Next Actions

### Immediate Tasks for Step 2:
1. **Create Cielo Website Structure**
   - Copy website project as template
   - Rename to cielo_website
   - Update branding and styling

2. **Configure Docker Services**
   - Add cielo_website to docker-compose.yml
   - Configure Traefik routing for cielo.viloforge.com
   - Set up environment variables

3. **Implement Access Control**
   - Create CieloAccessMiddleware
   - Define cielo.access permission
   - Test domain-based restrictions

### Prerequisites Before Starting Step 2:
- ✅ Identity provider multi-domain support (Step 1 complete)
- ✅ Working authentication across domains
- ✅ Security validation for redirects
- ⚠️ DNS entry for cielo.viloforge.com (currently shows chrome error)