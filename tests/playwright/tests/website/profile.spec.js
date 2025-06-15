const { test, expect } = require('@playwright/test');
const ApiClient = require('../../utils/api-client');
const TestHelpers = require('../../utils/helpers');

test.describe('Website Profile Page Tests', () => {
  let apiClient;
  let adminToken;

  test.beforeAll(async () => {
    apiClient = new ApiClient('local');
    
    // Get admin token for testing
    const adminUser = TestHelpers.getTestUser('admin');
    adminToken = await apiClient.authenticate(adminUser.username, adminUser.password);
    TestHelpers.log(`Got admin token for profile tests: ${adminToken.substring(0, 20)}...`, 'info');
  });

  test.describe('Login to Profile Flow Integration', () => {
    test('should complete full login to profile workflow', async ({ page }) => {
      // Step 1: Go to login page
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Step 2: Fill login form
      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');

      // Step 3: Submit login
      await page.click('button[type="submit"]');

      // Step 4: Should be redirected to home or profile
      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      // Step 5: Navigate to profile page
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Step 6: Verify both cookies are set
      const cookies = await page.context().cookies();
      const jwtCookie = cookies.find(c => c.name === 'jwt');
      const jwtTokenCookie = cookies.find(c => c.name === 'jwt_token');

      expect(jwtCookie).toBeDefined();
      expect(jwtTokenCookie).toBeDefined();
      expect(jwtCookie.httpOnly).toBe(true);
      expect(jwtTokenCookie.httpOnly).toBe(false);

      // Step 7: Verify profile loads successfully
      await expect(page.locator('#profile-content')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#profile-username')).toContainText('admin');

      TestHelpers.log('Verified complete login to profile workflow', 'info');
    });

    test('should handle profile access after login with remember me', async ({ page }) => {
      // Login with remember me checked
      await page.goto('https://localhost/accounts/login/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      await page.fill('input[name="email"]', 'admin');
      await page.fill('input[name="password"]', 'admin123');
      await page.check('input[name="remember"]');
      await page.click('button[type="submit"]');

      await page.waitForURL(/\/(accounts\/profile\/)?$/, { timeout: 10000 });

      // Navigate to profile
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Verify cookies have longer expiration (24 hours = 86400 seconds)
      const cookies = await page.context().cookies();
      const jwtCookie = cookies.find(c => c.name === 'jwt');
      const jwtTokenCookie = cookies.find(c => c.name === 'jwt_token');

      // Note: Playwright doesn't expose maxAge directly, but we can verify cookies exist
      expect(jwtCookie).toBeDefined();
      expect(jwtTokenCookie).toBeDefined();

      // Verify profile functionality works
      await expect(page.locator('#profile-content')).toBeVisible({ timeout: 10000 });

      TestHelpers.log('Verified login with remember me and profile access', 'info');
    });
  });

  test.describe('Profile Page Authentication', () => {
    test('should redirect to login when not authenticated', async ({ page }) => {
      // Navigate to profile page without authentication
      const response = await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should be redirected to login page
      expect(page.url()).toContain('/accounts/login/');
      expect(page.url()).toContain('next=/accounts/profile/');
      
      TestHelpers.log('Verified redirect to login for unauthenticated access', 'info');
    });

    test('should show profile page when authenticated with JWT cookies', async ({ page }) => {
      // Set both JWT cookies (the fix)
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }, {
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,  // JavaScript accessible
        secure: true,
        sameSite: 'Lax'
      }]);

      // Navigate to profile page
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should be on profile page
      expect(page.url()).toContain('/accounts/profile/');
      await expect(page.locator('h4.page-title')).toContainText('User Profile');
      
      TestHelpers.log('Verified profile page access with JWT authentication', 'info');
    });
  });

  test.describe('Profile Page Content', () => {
    test.beforeEach(async ({ page }) => {
      // Set both JWT cookies before each test
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }, {
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,  // JavaScript accessible
        secure: true,
        sameSite: 'Lax'
      }]);
    });

    test('should display profile page structure correctly', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check page title
      await expect(page).toHaveTitle('User Profile - VF Services');

      // Check main headings
      await expect(page.locator('h4.page-title')).toContainText('User Profile');
      await expect(page.locator('.card-title')).toContainText('Profile Information');

      // Check breadcrumb navigation
      await expect(page.locator('.breadcrumb')).toContainText('Dashboard');
      await expect(page.locator('.breadcrumb')).toContainText('Account');
      await expect(page.locator('.breadcrumb')).toContainText('Profile');

      TestHelpers.log('Verified profile page structure and headings', 'info');
    });

    test('should contain all required profile elements', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check for profile content elements
      await expect(page.locator('#profile-content')).toBeAttached();
      await expect(page.locator('#profile-loading')).toBeAttached();
      await expect(page.locator('#profile-error')).toBeAttached();
      await expect(page.locator('#profile-username')).toBeAttached();
      await expect(page.locator('#profile-email')).toBeAttached();
      await expect(page.locator('#refresh-profile-btn')).toBeAttached();

      TestHelpers.log('Verified all required profile elements are present', 'info');
    });

    test('should display account actions sidebar', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check account actions
      await expect(page.locator('text=Account Actions')).toBeVisible();
      await expect(page.locator('text=Logout')).toBeVisible();
      await expect(page.locator('text=Refresh Page')).toBeVisible();
      await expect(page.locator('text=Authentication Status')).toBeVisible();

      TestHelpers.log('Verified account actions sidebar is present', 'info');
    });
  });

  test.describe('Profile JavaScript Functionality', () => {
    test.beforeEach(async ({ page }) => {
      // Set both JWT cookies before each test (testing the fix)
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }, {
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,  // JavaScript accessible
        secure: true,
        sameSite: 'Lax'
      }]);
    });

    test('should load JavaScript configuration correctly', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check that JavaScript configuration is set
      const identityServiceUrl = await page.evaluate(() => {
        return window.IDENTITY_SERVICE_URL;
      });

      expect(identityServiceUrl).toBe('https://identity.vfservices.viloforge.com');

      TestHelpers.log('Verified JavaScript configuration is loaded correctly', 'info');
    });

    test('should initialize API client correctly', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for JavaScript to initialize
      await page.waitForFunction(() => {
        return window.profileApiClient && window.profileHandler;
      }, { timeout: 5000 });

      // Check that API client is available
      const hasApiClient = await page.evaluate(() => {
        return typeof window.profileApiClient !== 'undefined' && 
               typeof window.profileHandler !== 'undefined';
      });

      expect(hasApiClient).toBe(true);

      TestHelpers.log('Verified API client initialization', 'info');
    });

    test('should load profile data automatically', async ({ page }) => {
      // Listen for API requests
      const apiRequests = [];
      page.on('request', request => {
        if (request.url().includes('/api/profile/')) {
          apiRequests.push(request);
        }
      });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for profile content to be visible
      await expect(page.locator('#profile-content')).toBeVisible({ timeout: 10000 });

      // Check that profile data is loaded
      await expect(page.locator('#profile-username')).toContainText('admin');
      await expect(page.locator('#profile-email')).toContainText('@');

      // Verify API request was made
      expect(apiRequests.length).toBeGreaterThan(0);

      TestHelpers.log('Verified profile data loads automatically via API', 'info');
    });

    test('should handle refresh button functionality', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for initial load
      await expect(page.locator('#profile-content')).toBeVisible();

      // Track API requests
      let requestCount = 0;
      page.on('request', request => {
        if (request.url().includes('/api/profile/')) {
          requestCount++;
        }
      });

      // Click refresh button
      await page.locator('#refresh-profile-btn').click();

      // Wait for loading state
      await expect(page.locator('#profile-loading')).toBeVisible();
      
      // Wait for content to be visible again
      await expect(page.locator('#profile-content')).toBeVisible();

      // Should have made at least one more API request
      expect(requestCount).toBeGreaterThan(0);

      TestHelpers.log('Verified refresh button functionality', 'info');
    });

    test('should handle API errors gracefully', async ({ page }) => {
      // Block API requests to simulate error
      await page.route('**/api/profile/', route => {
        route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Internal server error' })
        });
      });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should show error state
      await expect(page.locator('#profile-error')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#profile-error-message')).toContainText('Internal server error');

      TestHelpers.log('Verified error handling for API failures', 'info');
    });

    test('should retry after API error', async ({ page }) => {
      let requestCount = 0;
      
      // Block first request, allow subsequent ones
      await page.route('**/api/profile/', route => {
        requestCount++;
        if (requestCount === 1) {
          route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ detail: 'Temporary error' })
          });
        } else {
          route.continue();
        }
      });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should show error first
      await expect(page.locator('#profile-error')).toBeVisible();

      // Click retry button
      await page.locator('#retry-profile-btn').click();

      // Should load successfully on retry
      await expect(page.locator('#profile-content')).toBeVisible();
      await expect(page.locator('#profile-username')).toContainText('admin');

      expect(requestCount).toBe(2);

      TestHelpers.log('Verified retry functionality after API error', 'info');
    });

    test('should fail gracefully when no JWT token is accessible to JavaScript', async ({ page }) => {
      // Set only httpOnly cookie (simulating the original bug)
      await page.context().clearCookies();
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,  // Only httpOnly cookie, no jwt_token
        secure: true,
        sameSite: 'Lax'
      }]);

      // Monitor console errors
      const consoleErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should show error state due to missing JavaScript-accessible token
      await expect(page.locator('#profile-error')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#profile-error-message')).toContainText('No authentication token found');

      // Check that appropriate console error was logged
      expect(consoleErrors.some(error => 
        error.includes('Failed to load profile') || 
        error.includes('No authentication token found')
      )).toBe(true);

      TestHelpers.log('Verified graceful handling of missing JavaScript-accessible token', 'info');
    });

    test('should successfully load profile with correct cookie setup', async ({ page }) => {
      // Monitor console logs to ensure no token errors
      const consoleLogs = [];
      page.on('console', msg => {
        consoleLogs.push({ type: msg.type(), text: msg.text() });
      });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should successfully load profile
      await expect(page.locator('#profile-content')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#profile-username')).toContainText('admin');

      // Check that token was found successfully
      expect(consoleLogs.some(log => 
        log.text.includes('Found JWT token in cookie')
      )).toBe(true);

      // Should not have token not found warnings
      expect(consoleLogs.some(log => 
        log.text.includes('JWT token not found in cookies')
      )).toBe(false);

      TestHelpers.log('Verified successful profile loading with correct token setup', 'info');
    });
  });

  test.describe('Profile Page Security', () => {
    test('should not expose sensitive information', async ({ page }) => {
      // Set JWT cookie
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }]);

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Wait for profile to load
      await expect(page.locator('#profile-content')).toBeVisible();

      // Check that page doesn't contain sensitive information
      const pageContent = await page.content();
      expect(pageContent).not.toContain('password');
      expect(pageContent).not.toContain('secret');
      expect(pageContent).not.toContain('private_key');

      TestHelpers.log('Verified no sensitive information is exposed', 'info');
    });

    test('should handle invalid JWT tokens', async ({ page }) => {
      // Set invalid JWT cookie
      await page.context().addCookies([{
        name: 'jwt',
        value: 'invalid-jwt-token',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }]);

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Should either redirect to login or show error
      const currentUrl = page.url();
      if (currentUrl.includes('/accounts/login/')) {
        TestHelpers.log('Invalid JWT redirected to login page', 'info');
      } else {
        // If not redirected, should show error in profile loading
        await expect(page.locator('#profile-error')).toBeVisible({ timeout: 10000 });
        TestHelpers.log('Invalid JWT handled with error display', 'info');
      }
    });
  });

  test.describe('Profile Page Navigation', () => {
    test.beforeEach(async ({ page }) => {
      // Set both JWT cookies before each test
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }, {
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,  // JavaScript accessible
        secure: true,
        sameSite: 'Lax'
      }]);
    });

    test('should have working logout functionality', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check logout link exists
      const logoutLink = page.locator('a[href="/accounts/logout/"]');
      await expect(logoutLink).toBeVisible();

      TestHelpers.log('Verified logout link is present and accessible', 'info');
    });

    test('should have working refresh page functionality', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check refresh button exists
      const refreshButton = page.locator('button:has-text("Refresh Page")');
      await expect(refreshButton).toBeVisible();

      // Test refresh functionality
      await refreshButton.click();
      await page.waitForLoadState('networkidle');

      // Should still be on profile page
      expect(page.url()).toContain('/accounts/profile/');

      TestHelpers.log('Verified refresh page functionality', 'info');
    });

    test('should display service information correctly', async ({ page }) => {
      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check service information section
      await expect(page.locator('text=Service Information')).toBeVisible();
      await expect(page.locator('#identity-service-url')).toContainText('identity.vfservices.viloforge.com');

      TestHelpers.log('Verified service information is displayed correctly', 'info');
    });
  });

  test.describe('Profile Page Responsive Design', () => {
    test.beforeEach(async ({ page }) => {
      // Set both JWT cookies before each test
      await page.context().addCookies([{
        name: 'jwt',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: true,
        sameSite: 'Lax'
      }, {
        name: 'jwt_token',
        value: adminToken,
        domain: 'localhost',
        path: '/',
        httpOnly: false,  // JavaScript accessible
        secure: true,
        sameSite: 'Lax'
      }]);
    });

    test('should be responsive on mobile devices', async ({ page }) => {
      // Set mobile viewport
      await page.setViewportSize({ width: 375, height: 667 });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check that content is still visible and accessible
      await expect(page.locator('h4.page-title')).toBeVisible();
      await expect(page.locator('#refresh-profile-btn')).toBeVisible();

      TestHelpers.log('Verified responsive design on mobile viewport', 'info');
    });

    test('should be responsive on tablet devices', async ({ page }) => {
      // Set tablet viewport
      await page.setViewportSize({ width: 768, height: 1024 });

      await page.goto('https://localhost/accounts/profile/', {
        waitUntil: 'networkidle',
        timeout: 10000
      });

      // Check that layout adapts properly
      await expect(page.locator('.col-lg-8')).toBeVisible();
      await expect(page.locator('.col-lg-4')).toBeVisible();

      TestHelpers.log('Verified responsive design on tablet viewport', 'info');
    });
  });
});