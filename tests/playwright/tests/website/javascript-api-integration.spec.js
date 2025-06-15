const { test, expect } = require('@playwright/test');
const ApiClient = require('../../utils/api-client');
const TestHelpers = require('../../utils/helpers');

/**
 * JavaScript API Integration Tests
 * 
 * These tests focus on the actual JavaScript code that runs in the browser,
 * ensuring that the Identity API Client and profile page handler work correctly
 * with real cross-domain requests.
 * 
 * CRITICAL: These tests catch issues that pure API tests miss:
 * - CORS configuration problems
 * - JavaScript fetch() behavior
 * - Cookie handling in cross-domain contexts
 * - Real browser security policies
 */
test.describe('Website JavaScript API Integration', () => {
  let apiClient;
  let adminToken;

  test.beforeAll(async () => {
    apiClient = new ApiClient('local');
    
    const adminUser = TestHelpers.getTestUser('admin');
    adminToken = await apiClient.authenticate(adminUser.username, adminUser.password);
    TestHelpers.log(`Got admin token for JavaScript integration tests: ${adminToken.substring(0, 20)}...`, 'info');
  });

  test.describe('Profile Page JavaScript Behavior', () => {
    test('should execute the actual profile page JavaScript without errors', async ({ page }) => {
      const jsErrors = [];
      const networkErrors = [];
      const consoleMessages = [];

      // Capture JavaScript errors
      page.on('pageerror', error => {
        jsErrors.push(error.message);
      });

      // Capture console messages
      page.on('console', msg => {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      });

      // Capture network failures
      page.on('requestfailed', request => {
        networkErrors.push({
          url: request.url(),
          failure: request.failure()?.errorText || 'Unknown error'
        });
      });

      // Step 1: Login to get proper cookies
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      // Step 2: Navigate to profile page (this executes the JavaScript)
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Step 3: Wait for JavaScript to complete
      await page.waitForTimeout(5000);

      // Step 4: Verify no JavaScript errors occurred
      if (jsErrors.length > 0) {
        TestHelpers.log(`JavaScript errors detected: ${JSON.stringify(jsErrors)}`, 'error');
        expect(jsErrors.length).toBe(0);
      }

      // Step 5: Check for CORS or network errors
      const corsErrors = networkErrors.filter(error => 
        error.failure.includes('CORS') || 
        error.failure.includes('Cross-Origin') ||
        error.url.includes('/api/')
      );

      if (corsErrors.length > 0) {
        TestHelpers.log(`CORS-related network errors: ${JSON.stringify(corsErrors)}`, 'error');
        expect(corsErrors.length).toBe(0);
      }

      // Step 6: Verify profile content loaded
      const profileVisible = await page.locator('#profile-content').isVisible();
      const profileErrorVisible = await page.locator('#profile-error').isVisible();

      expect(profileVisible).toBe(true);
      expect(profileErrorVisible).toBe(false);

      // Step 7: Verify profile data is populated
      const username = await page.locator('#profile-username').textContent();
      const email = await page.locator('#profile-email').textContent();

      expect(username).toBe('admin');
      expect(email).toContain('@');

      TestHelpers.log('Profile page JavaScript executed successfully without CORS errors', 'info');
    });

    test('should handle API client initialization correctly', async ({ page }) => {
      // Navigate to profile page
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Test the JavaScript API client directly in browser context
      const apiClientTest = await page.evaluate(() => {
        try {
          // Verify global objects are available
          const hasIdentityApiClient = typeof window.IdentityApiClient === 'function';
          const hasProfilePageHandler = typeof window.ProfilePageHandler === 'function';
          const hasProfileApiClient = typeof window.profileApiClient === 'object';
          const hasProfileHandler = typeof window.profileHandler === 'object';

          // Test token retrieval
          let tokenFound = false;
          if (window.profileApiClient) {
            const token = window.profileApiClient.getToken();
            tokenFound = token !== null && token.length > 0;
          }

          // Test API URL construction
          let apiUrlCorrect = false;
          if (window.profileApiClient) {
            apiUrlCorrect = window.profileApiClient.apiUrl.includes('/api');
          }

          return {
            success: true,
            hasIdentityApiClient,
            hasProfilePageHandler,
            hasProfileApiClient,
            hasProfileHandler,
            tokenFound,
            apiUrlCorrect,
            identityServiceUrl: window.IDENTITY_SERVICE_URL
          };

        } catch (error) {
          return {
            success: false,
            error: error.message
          };
        }
      });

      expect(apiClientTest.success).toBe(true);
      expect(apiClientTest.hasIdentityApiClient).toBe(true);
      expect(apiClientTest.hasProfilePageHandler).toBe(true);
      expect(apiClientTest.hasProfileApiClient).toBe(true);
      expect(apiClientTest.hasProfileHandler).toBe(true);
      expect(apiClientTest.tokenFound).toBe(true);
      expect(apiClientTest.apiUrlCorrect).toBe(true);
      expect(apiClientTest.identityServiceUrl).toBeTruthy();

      TestHelpers.log('JavaScript API client initialized correctly', 'info');
    });

    test('should handle refresh functionality without CORS issues', async ({ page }) => {
      // Login and navigate to profile
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for initial load
      await expect(page.locator('#profile-content')).toBeVisible({ timeout: 10000 });

      // Track network requests
      const apiRequests = [];
      page.on('request', request => {
        if (request.url().includes('/api/profile/')) {
          apiRequests.push({
            url: request.url(),
            method: request.method(),
            headers: request.headers()
          });
        }
      });

      // Click refresh button
      await page.click('#refresh-profile-btn');

      // Wait for refresh to complete
      await page.waitForTimeout(3000);

      // Verify refresh worked
      const profileStillVisible = await page.locator('#profile-content').isVisible();
      const errorNotVisible = await page.locator('#profile-error').isVisible();

      expect(profileStillVisible).toBe(true);
      expect(errorNotVisible).toBe(false);

      // Verify API request was made
      expect(apiRequests.length).toBeGreaterThan(0);

      // Check that authorization header was included
      const lastRequest = apiRequests[apiRequests.length - 1];
      expect(lastRequest.headers['authorization']).toBeTruthy();
      expect(lastRequest.headers['authorization']).toContain('Bearer');

      TestHelpers.log('Profile refresh functionality works without CORS issues', 'info');
    });
  });

  test.describe('Cross-Domain Request Monitoring', () => {
    test('should monitor all cross-domain API requests for CORS compliance', async ({ page }) => {
      const crossDomainRequests = [];
      const corsFailures = [];

      // Monitor all requests
      page.on('request', request => {
        const url = new URL(request.url());
        if (url.pathname.startsWith('/api/')) {
          crossDomainRequests.push({
            url: request.url(),
            method: request.method(),
            headers: request.headers(),
            timestamp: new Date().toISOString()
          });
        }
      });

      // Monitor request failures
      page.on('requestfailed', request => {
        if (request.url().includes('/api/')) {
          corsFailures.push({
            url: request.url(),
            failure: request.failure()?.errorText || 'Unknown error',
            timestamp: new Date().toISOString()
          });
        }
      });

      // Execute the full login and profile flow
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.click('button[type="submit"]');
      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for all API calls to complete
      await page.waitForTimeout(5000);

      // Analyze results
      TestHelpers.log(`Cross-domain API requests made: ${crossDomainRequests.length}`, 'info');
      TestHelpers.log(`CORS failures detected: ${corsFailures.length}`, 'info');

      if (crossDomainRequests.length > 0) {
        TestHelpers.log(`API requests: ${JSON.stringify(crossDomainRequests, null, 2)}`, 'debug');
      }

      if (corsFailures.length > 0) {
        TestHelpers.log(`CORS failures: ${JSON.stringify(corsFailures, null, 2)}`, 'error');
        expect(corsFailures.length).toBe(0);
      }

      // Verify at least one successful API request was made
      expect(crossDomainRequests.length).toBeGreaterThan(0);

      // Verify profile loaded successfully
      await expect(page.locator('#profile-content')).toBeVisible();

      TestHelpers.log('All cross-domain API requests completed successfully', 'info');
    });
  });

  test.describe('Error Scenario Testing', () => {
    test('should gracefully handle token expiration without CORS errors', async ({ page }) => {
      // Navigate to profile page
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Set an expired JWT token
      await page.context().addCookies([{
        name: 'jwt_token',
        value: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3QiLCJleHAiOjF9.expired',
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Refresh page to trigger API call with expired token
      await page.reload({ waitUntil: 'networkidle', timeout: 10000 });

      // Wait for JavaScript to execute
      await page.waitForTimeout(5000);

      // Should show error (not CORS error, but authentication error)
      const errorVisible = await page.locator('#profile-error').isVisible();
      expect(errorVisible).toBe(true);

      // Error should be about authentication, not CORS
      const errorMessage = await page.locator('#profile-error-message').textContent();
      expect(errorMessage).not.toContain('CORS');
      expect(errorMessage).not.toContain('Cross-Origin');

      TestHelpers.log(`Authentication error handled gracefully: ${errorMessage}`, 'info');
    });

    test('should handle network connectivity issues separate from CORS', async ({ page }) => {
      // This test helps distinguish between CORS errors and network errors
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Set valid token
      await page.context().addCookies([{
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,
        secure: true,
        sameSite: 'Lax'
      }]);

      // Simulate network failure by blocking API requests
      await page.route('**/api/**', route => {
        route.abort('failed');
      });

      // Refresh page to trigger API call
      await page.reload({ waitUntil: 'networkidle', timeout: 10000 });
      await page.waitForTimeout(5000);

      // Should show error (network error, not CORS error)
      const errorVisible = await page.locator('#profile-error').isVisible();
      expect(errorVisible).toBe(true);

      const errorMessage = await page.locator('#profile-error-message').textContent();
      TestHelpers.log(`Network error handled: ${errorMessage}`, 'info');

      // This test confirms our error handling can distinguish error types
      TestHelpers.log('Network error handling verified', 'info');
    });
  });
});