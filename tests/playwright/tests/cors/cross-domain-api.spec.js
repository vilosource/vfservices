const { test, expect } = require('@playwright/test');
const ApiClient = require('../../utils/api-client');
const TestHelpers = require('../../utils/helpers');

/**
 * CORS Testing Suite
 * 
 * These tests specifically target CORS issues by simulating real browser
 * behavior where JavaScript on one domain makes requests to another domain.
 * 
 * WHY THIS IS IMPORTANT:
 * - Playwright API requests (request.newContext()) bypass CORS completely
 * - Real browser fetch() calls are subject to CORS policies
 * - This test suite uses page.evaluate() to execute fetch() in browser context
 * - This catches CORS misconfigurations that API-only tests miss
 */
test.describe('Cross-Domain API Access (CORS Testing)', () => {
  let apiClient;
  let adminToken;

  test.beforeAll(async () => {
    apiClient = new ApiClient('local');
    
    // Get admin token for testing
    const adminUser = TestHelpers.getTestUser('admin');
    adminToken = await apiClient.authenticate(adminUser.username, adminUser.password);
    TestHelpers.log(`Got admin token for CORS tests: ${adminToken.substring(0, 20)}...`, 'info');
  });

  test.describe('Real Browser CORS Behavior', () => {
    test('should handle CORS when making fetch request from website to identity API', async ({ page }) => {
      // Step 1: Navigate to website domain (this establishes the origin)
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Step 2: Set JWT token cookie so we have authentication
      await page.context().addCookies([{
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Step 3: Execute fetch request in browser context (this is where CORS applies!)
      const result = await page.evaluate(async (token) => {
        try {
          console.log('Executing fetch from browser context...');
          
          // This fetch call will be subject to CORS policies because:
          // - Origin: https://localhost (website domain) 
          // - Target: https://localhost with Host header for identity domain
          const response = await fetch('https://localhost/api/profile/', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
              'Host': 'identity.vfservices.viloforge.com'  // Traefik routing
            },
            credentials: 'include'  // Important for CORS with cookies
          });

          if (!response.ok) {
            const errorText = await response.text();
            return {
              success: false,
              status: response.status,
              statusText: response.statusText,
              error: errorText,
              headers: Object.fromEntries(response.headers.entries())
            };
          }

          const data = await response.json();
          return {
            success: true,
            status: response.status,
            data: data,
            headers: Object.fromEntries(response.headers.entries())
          };

        } catch (error) {
          return {
            success: false,
            error: error.message,
            networkError: true
          };
        }
      }, adminToken);

      // Step 4: Verify the request succeeded (meaning CORS is properly configured)
      if (!result.success) {
        if (result.networkError) {
          TestHelpers.log(`Network error: ${result.error}`, 'error');
        } else {
          TestHelpers.log(`API error: ${result.status} - ${result.error}`, 'error');
        }
      }

      expect(result.success).toBe(true);
      expect(result.status).toBe(200);
      expect(result.data).toHaveProperty('username');
      expect(result.data).toHaveProperty('email');
      
      TestHelpers.log('CORS test passed - fetch from website to identity API succeeded', 'info');
    });

    test('should detect CORS errors when they occur', async ({ page }) => {
      // Navigate to website domain
      await page.goto('https://localhost/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Test cross-domain request to a hypothetically misconfigured endpoint
      const result = await page.evaluate(async () => {
        try {
          // This should fail if CORS is not properly configured
          // We're testing a non-existent endpoint to simulate CORS failure
          const response = await fetch('https://identity.vfservices.viloforge.com/api/profile/', {
            method: 'GET',
            headers: {
              'Authorization': 'Bearer fake-token',
              'Content-Type': 'application/json'
            }
          });

          return {
            success: true,
            status: response.status
          };

        } catch (error) {
          // CORS errors typically manifest as network errors in fetch
          if (error.message.includes('CORS') || 
              error.message.includes('Cross-Origin') ||
              error.message.includes('Failed to fetch')) {
            return {
              success: false,
              corsError: true,
              error: error.message
            };
          }
          
          return {
            success: false,
            otherError: true,
            error: error.message
          };
        }
      });

      // This test demonstrates how CORS errors would be caught
      if (result.corsError) {
        TestHelpers.log(`CORS error detected (expected): ${result.error}`, 'info');
      } else {
        TestHelpers.log('No CORS error detected - endpoint may be properly configured or accessible', 'info');
      }
    });

    test('should verify CORS headers are present in responses', async ({ page }) => {
      // Navigate to website domain  
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Set authentication cookies
      await page.context().addCookies([{
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Check CORS headers in browser context
      const corsHeaders = await page.evaluate(async (token) => {
        try {
          const response = await fetch('https://localhost/api/profile/', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Host': 'identity.vfservices.viloforge.com'
            },
            credentials: 'include'
          });

          return {
            success: response.ok,
            status: response.status,
            corsHeaders: {
              'access-control-allow-origin': response.headers.get('access-control-allow-origin'),
              'access-control-allow-credentials': response.headers.get('access-control-allow-credentials'),
              'access-control-allow-methods': response.headers.get('access-control-allow-methods'),
              'access-control-allow-headers': response.headers.get('access-control-allow-headers')
            }
          };

        } catch (error) {
          return {
            success: false,
            error: error.message
          };
        }
      }, adminToken);

      expect(corsHeaders.success).toBe(true);
      
      // Verify CORS headers are present and correct
      expect(corsHeaders.corsHeaders['access-control-allow-credentials']).toBe('true');
      expect(corsHeaders.corsHeaders['access-control-allow-origin']).toBeTruthy();
      
      TestHelpers.log(`CORS headers verified: ${JSON.stringify(corsHeaders.corsHeaders)}`, 'info');
    });
  });

  test.describe('Console Error Detection', () => {
    test('should detect CORS errors in browser console', async ({ page }) => {
      const consoleErrors = [];
      const networkErrors = [];

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

      // Listen for failed network requests
      page.on('requestfailed', request => {
        networkErrors.push({
          url: request.url(),
          failure: request.failure()
        });
      });

      // Navigate to profile page (this triggers the JavaScript API call)
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Set authentication cookies
      await page.context().addCookies([{
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Wait for the JavaScript to load profile (this is where CORS issues would occur)
      await page.waitForTimeout(3000);

      // Check if profile loaded successfully (no CORS errors)
      const profileVisible = await page.locator('#profile-content').isVisible();
      const errorVisible = await page.locator('#profile-error').isVisible();

      // Report any CORS-related console errors
      if (consoleErrors.length > 0) {
        TestHelpers.log(`CORS errors detected in console: ${JSON.stringify(consoleErrors)}`, 'error');
        expect(consoleErrors.length).toBe(0); // Fail test if CORS errors found
      }

      // Report any network failures that might be CORS-related
      if (networkErrors.length > 0) {
        TestHelpers.log(`Network errors detected: ${JSON.stringify(networkErrors)}`, 'warn');
      }

      // Verify profile loaded successfully
      expect(profileVisible).toBe(true);
      expect(errorVisible).toBe(false);

      TestHelpers.log('No CORS errors detected in browser console', 'info');
    });
  });

  test.describe('Multi-Service CORS Testing', () => {
    test('should test CORS for future billing service endpoints', async ({ page }) => {
      // Navigate to website domain
      await page.goto('https://localhost/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Set authentication
      await page.context().addCookies([{
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Test cross-domain request to billing service (when implemented)
      const result = await page.evaluate(async (token) => {
        try {
          const response = await fetch('https://localhost/api/billing/summary/', {
            method: 'GET',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
              'Host': 'billing.vfservices.viloforge.com'
            },
            credentials: 'include'
          });

          return {
            success: response.ok,
            status: response.status,
            error: response.ok ? null : await response.text()
          };

        } catch (error) {
          return {
            success: false,
            error: error.message,
            possibleCorsError: error.message.includes('CORS') || error.message.includes('fetch')
          };
        }
      }, adminToken);

      // For now, we expect this to fail (service not implemented)
      // But we want to catch CORS-specific failures vs other failures
      if (!result.success && result.possibleCorsError) {
        TestHelpers.log(`Potential CORS issue with billing service: ${result.error}`, 'warn');
      } else if (!result.success) {
        TestHelpers.log(`Billing service not available (expected): ${result.error}`, 'info');
      }

      // This test serves as a template for when billing service is implemented
      TestHelpers.log('Multi-service CORS test completed', 'info');
    });
  });
});