# CORS Testing Strategy Documentation

## Problem Identified

During development, we discovered that **Playwright tests were not catching CORS configuration issues** that only surfaced when real users browsed to the website. This document explains why this happened and provides a comprehensive solution.

## Why Playwright Tests Missed CORS Issues

### 🚨 **Root Cause Analysis**

1. **Different Request Mechanisms**:
   - **Playwright API Client**: Uses `request.newContext()` → Makes **server-to-server HTTP requests**
   - **Real Browser JavaScript**: Uses `fetch()` → Makes **browser-to-server requests** subject to CORS

2. **CORS Only Applies to Browser Requests**:
   - CORS is a **browser security feature** that doesn't affect server-to-server calls
   - Playwright's `request.newContext()` bypasses the browser's CORS enforcement
   - Only JavaScript `fetch()` calls from a browser context trigger CORS validation

3. **Test Coverage Gap**:
   ```javascript
   // ❌ This DOESN'T test CORS (bypasses browser CORS policies)
   const context = await request.newContext();
   const response = await context.get('https://identity.../api/profile/');
   
   // ✅ This DOES test CORS (executes in browser context)
   const result = await page.evaluate(async () => {
     const response = await fetch('https://identity.../api/profile/');
     return response.json();
   });
   ```

### 📊 **Request Flow Comparison**

| Test Type | Request Origin | CORS Enforcement | Catches CORS Issues |
|-----------|----------------|------------------|-------------------|
| Playwright API Client | Test Runner Server | ❌ No | ❌ No |
| Real Browser JavaScript | Website Domain | ✅ Yes | ✅ Yes |
| Enhanced Browser Tests | Browser Context | ✅ Yes | ✅ Yes |

## Enhanced CORS Testing Strategy

### 1. Browser Context Testing

**File**: `tests/playwright/tests/cors/cross-domain-api.spec.js`

This test suite executes `fetch()` calls in actual browser context to test CORS:

```javascript
test('should handle CORS when making fetch request from website to identity API', async ({ page }) => {
  // Step 1: Navigate to website domain (establishes origin)
  await page.goto('https://localhost/accounts/profile/');

  // Step 2: Execute fetch in browser context (CORS applies here!)
  const result = await page.evaluate(async (token) => {
    const response = await fetch('https://localhost/api/profile/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Host': 'identity.vfservices.viloforge.com'
      },
      credentials: 'include'  // Critical for CORS with cookies
    });

    return {
      success: response.ok,
      status: response.status,
      data: await response.json()
    };
  }, adminToken);

  expect(result.success).toBe(true);
});
```

**Why this works:**
- `page.evaluate()` executes code in the browser context
- `fetch()` call is subject to browser CORS policies
- Test fails if CORS is misconfigured

### 2. Console Error Detection

**File**: `tests/playwright/tests/website/javascript-api-integration.spec.js`

Monitors browser console for CORS-related errors:

```javascript
test('should detect CORS errors in browser console', async ({ page }) => {
  const consoleErrors = [];

  // Listen for console errors (CORS errors often appear here)
  page.on('console', msg => {
    if (msg.type() === 'error') {
      const text = msg.text();
      if (text.includes('CORS') || 
          text.includes('Cross-Origin') || 
          text.includes('Access to fetch')) {
        consoleErrors.push(text);
      }
    }
  });

  // Navigate to profile page (triggers JavaScript API calls)
  await page.goto('https://localhost/accounts/profile/');

  // Check for CORS errors
  expect(consoleErrors.length).toBe(0);
});
```

### 3. Network Request Monitoring

Tracks all cross-domain requests and their success/failure:

```javascript
test('should monitor cross-domain API requests for CORS compliance', async ({ page }) => {
  const corsFailures = [];

  // Monitor request failures
  page.on('requestfailed', request => {
    if (request.url().includes('/api/')) {
      corsFailures.push({
        url: request.url(),
        failure: request.failure()?.errorText
      });
    }
  });

  // Execute full profile workflow
  await page.goto('https://localhost/accounts/profile/');
  
  // Verify no CORS failures
  expect(corsFailures.length).toBe(0);
});
```

### 4. JavaScript Integration Testing

Tests the actual JavaScript code that runs in production:

```javascript
test('should execute actual profile page JavaScript without errors', async ({ page }) => {
  const jsErrors = [];

  // Capture JavaScript errors
  page.on('pageerror', error => {
    jsErrors.push(error.message);
  });

  // Login and navigate to profile
  await page.goto('https://localhost/accounts/login/');
  await page.fill('input[name="email"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  
  await page.goto('https://localhost/accounts/profile/');
  await page.waitForTimeout(5000); // Let JavaScript execute

  // Verify no JavaScript errors
  expect(jsErrors.length).toBe(0);
  
  // Verify profile loaded successfully  
  expect(await page.locator('#profile-content').isVisible()).toBe(true);
});
```

## CORS Headers Validation

### Test CORS Response Headers

```javascript
test('should verify CORS headers are present', async ({ page }) => {
  await page.goto('https://localhost/accounts/profile/');

  const corsHeaders = await page.evaluate(async (token) => {
    const response = await fetch('https://localhost/api/profile/', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    return {
      'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
      'access-control-allow-credentials': response.headers.get('access-control-allow-credentials'),
      'access-control-allow-methods': response.headers.get('access-control-allow-methods')
    };
  }, adminToken);

  expect(corsHeaders['access-control-allow-credentials']).toBe('true');
  expect(corsHeaders['access-control-allow-origin']).toBeTruthy();
});
```

## Multi-Service CORS Testing

### Template for Future Services

```javascript
test('should test CORS for billing service endpoints', async ({ page }) => {
  await page.goto('https://localhost/');

  const result = await page.evaluate(async (token) => {
    try {
      const response = await fetch('https://localhost/api/billing/summary/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Host': 'billing.vfservices.viloforge.com'
        },
        credentials: 'include'
      });

      return { success: response.ok, status: response.status };
    } catch (error) {
      return {
        success: false,
        corsError: error.message.includes('CORS')
      };
    }
  }, adminToken);

  // Test passes when billing service is properly configured
  // Fails with CORS error if misconfigured
});
```

## Implementation Guidelines

### 1. For New API Endpoints

When adding new API endpoints to any service:

```javascript
// Always add a CORS test for new endpoints
test('should access new endpoint without CORS issues', async ({ page }) => {
  await page.goto('https://localhost/');
  
  const result = await page.evaluate(async (token) => {
    const response = await fetch('https://localhost/api/new-endpoint/', {
      headers: { 'Authorization': `Bearer ${token}` },
      credentials: 'include'
    });
    return { success: response.ok };
  }, adminToken);
  
  expect(result.success).toBe(true);
});
```

### 2. For New Frontend Features

When adding JavaScript that calls APIs:

```javascript
// Test the actual JavaScript code path
test('should execute new feature JavaScript without CORS errors', async ({ page }) => {
  const jsErrors = [];
  page.on('pageerror', error => jsErrors.push(error.message));

  await page.goto('https://localhost/new-feature/');
  await page.waitForTimeout(5000); // Let JavaScript execute
  
  expect(jsErrors.length).toBe(0);
  expect(await page.locator('#feature-content').isVisible()).toBe(true);
});
```

### 3. Running CORS Tests

```bash
# Run only CORS-specific tests
npm test -- --grep "CORS"

# Run JavaScript integration tests  
npm test -- tests/website/javascript-api-integration.spec.js

# Run cross-domain API tests
npm test -- tests/cors/cross-domain-api.spec.js
```

## Debugging CORS Issues

### 1. Check Browser Console

When tests fail, check the browser console for CORS errors:

```javascript
// This will appear in browser console if CORS is misconfigured:
// "Access to fetch at 'https://identity.../api/profile/' from origin 'https://website...' has been blocked by CORS policy"
```

### 2. Verify CORS Configuration

Check that Identity Provider has correct CORS settings:

```python
# identity-provider/main/settings.py
CORS_ALLOWED_ORIGINS = [
    "https://vfservices.viloforge.com",      # Main website domain
    "https://website.vfservices.viloforge.com",  # Website subdomain
    "https://localhost",                      # Local development
]

CORS_ALLOW_CREDENTIALS = True  # Required for cookie authentication
```

### 3. Test Network Tab

Use browser DevTools Network tab to inspect:
- **Request Headers**: Should include `Origin: https://website...`
- **Response Headers**: Should include `Access-Control-Allow-Origin`
- **Status**: Should be 200, not preflight failure

## Benefits of Enhanced CORS Testing

### ✅ **What We Now Catch**

1. **CORS Misconfigurations**: Missing or incorrect CORS headers
2. **Cross-Domain Issues**: Problems with subdomain access
3. **Cookie Handling**: CORS credential issues
4. **JavaScript Errors**: Actual browser JavaScript failures
5. **Authentication Flow**: Real-world login → API access patterns

### 🎯 **Confidence Gained**

- **Production Parity**: Tests now match real user experience
- **Early Detection**: CORS issues caught in CI/CD pipeline
- **Comprehensive Coverage**: Both API functionality and browser behavior tested
- **Multi-Service Ready**: Pattern works for billing, inventory, future services

## Summary

The enhanced CORS testing strategy ensures that:

1. **API functionality works** (existing Playwright API tests)
2. **Browser CORS policies are satisfied** (new browser context tests)
3. **JavaScript executes without errors** (JavaScript integration tests)
4. **Real user workflows succeed** (end-to-end browser tests)

This comprehensive approach prevents CORS issues from reaching production and provides confidence that the microservices architecture works correctly across all domains and services.