# Cielo Step 2 Testing Guide

## Overview

This guide covers testing for Step 2 of the Cielo implementation: Create Cielo Website Base. The tests verify that the Cielo website is properly configured with authentication and access control.

## Prerequisites

Before running tests, ensure:

1. **Services are running:**
   ```bash
   docker-compose up -d postgres redis identity-provider website cielo-website
   ```

2. **Database migrations completed:**
   ```bash
   docker-compose exec cielo-website python manage.py migrate
   ```

3. **Test dependencies installed:**
   ```bash
   pip install playwright requests
   python -m playwright install chromium
   ```

## Available Test Scripts

### 1. Simple Playwright Test
**File:** `tests/playwright/basic/test_cielo_step2_playwright_simple.py`

Quick browser-based test for basic functionality:
```bash
# Run headless (no browser window)
python tests/playwright/basic/test_cielo_step2_playwright_simple.py

# Run with browser window visible
python tests/playwright/basic/test_cielo_step2_playwright_simple.py --headed
```

**Tests:**
- ✅ Unauthenticated redirect to login
- ✅ Access denied for users without cielo.access permission
- ✅ Cielo branding in URLs
- ✅ SSO cookie configuration
- ✅ CORS configuration

### 2. Comprehensive Playwright Test Suite
**File:** `tests/playwright/e2e/test_cielo_step2_playwright.py`

Full test suite with detailed scenarios:
```bash
# Run with pytest
pytest tests/playwright/e2e/test_cielo_step2_playwright.py -v

# Run standalone (if pytest not available)
python tests/playwright/e2e/test_cielo_step2_playwright.py
```

**Tests:**
- Unauthenticated redirect
- Access control (no permission)
- Branding elements
- SSO cookie configuration
- CORS configuration
- Middleware chain
- Static files
- Logout functionality
- Error handling
- Security headers

### 3. API-Level Access Control Test
**File:** `tests/playwright/api/test_cielo_step2_access.py`

Tests authentication and access control at the API level:
```bash
python tests/playwright/api/test_cielo_step2_access.py
```

**Tests:**
- ✅ Unauthenticated access redirect
- ✅ JWT token authentication
- ✅ Access control for users without permission
- ✅ Cookie-based authentication
- ✅ Service health check
- ✅ CORS headers
- ✅ Redirect security

## Manual Testing Steps

### 1. Test Unauthenticated Access
1. Open browser to https://cielo.vfservices.viloforge.com
2. **Expected:** Redirect to https://identity.vfservices.viloforge.com/accounts/login/?redirect_uri=https://cielo.vfservices.viloforge.com/
3. **Verify:** Login form is displayed

### 2. Test Access Without Permission
1. Login as alice (password: password123)
2. **Expected:** Redirect to https://www.vfservices.viloforge.com/
3. **Verify:** NOT on cielo.vfservices.viloforge.com

### 3. Test Logout
1. If logged in, go to https://identity.vfservices.viloforge.com/accounts/logout/
2. Try accessing https://cielo.vfservices.viloforge.com again
3. **Expected:** Redirect to login page

### 4. Test Static Files
1. Access https://cielo.vfservices.viloforge.com/static/assets/css/app.min.css
2. **Expected:** CSS file loads or redirects to login (both acceptable at this stage)

## Expected Test Results

### Current Status (Step 2)
- ✅ Cielo website service created and configured
- ✅ Authentication redirects working
- ✅ CieloAccessMiddleware blocks users without permission
- ✅ SSO cookies configured for cross-domain
- ✅ CORS allows cielo domain

### Limitations (Until Step 3)
- ❌ No users have cielo.access permission yet
- ❌ Cannot test successful Cielo access
- ❌ Menu system not yet implemented

## Debugging Common Issues

### 1. Service Not Running
```bash
# Check if cielo-website is running
docker-compose ps cielo-website

# View logs
docker-compose logs -f cielo-website
```

### 2. Database Not Migrated
```bash
docker-compose exec cielo-website python manage.py migrate
```

### 3. CORS Errors
Check browser console for CORS errors. Identity provider should include cielo domain in CORS_ALLOWED_ORIGINS.

### 4. Cookie Issues
- Check browser developer tools → Application → Cookies
- SSO cookie should have domain: .vfservices.viloforge.com

### 5. Redirect Issues
- Check redirect_uri parameter in URL
- Verify ALLOWED_REDIRECT_DOMAINS in identity provider settings

## Test Summary

| Test Category | Simple | Comprehensive | API-Level |
|--------------|---------|---------------|-----------|
| Unauthenticated Redirect | ✅ | ✅ | ✅ |
| Access Control | ✅ | ✅ | ✅ |
| Cookie/JWT Auth | ✅ | ✅ | ✅ |
| CORS Configuration | ✅ | ✅ | ✅ |
| Service Health | - | ✅ | ✅ |
| Security Headers | - | ✅ | - |
| Error Handling | - | ✅ | - |

## Next Steps

After Step 2 tests pass:
1. Proceed to Step 3: Add test users (Mary & Paul)
2. Mary will have vfservices access only
3. Paul will have cielo.access permission
4. This will enable full Cielo access testing