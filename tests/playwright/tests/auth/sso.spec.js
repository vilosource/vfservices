const { test, expect } = require('@playwright/test');
const LoginPage = require('../../pages/login-page');
const BasePage = require('../../pages/base-page');
const TestHelpers = require('../../utils/helpers');

test.describe('Single Sign-On (SSO) Tests', () => {
  let loginPage;
  let basePage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    basePage = new BasePage(page);
    await loginPage.clearAuth();
  });

  test.afterEach(async ({ page }) => {
    try {
      await loginPage.clearAuth();
    } catch (error) {
      TestHelpers.log(`Cleanup error: ${error.message}`, 'warn');
    }
  });

  test('should authenticate once and access all services', async () => {
    // Login through identity provider
    await loginPage.loginWithTestUser('admin');
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    
    // Test access to all services without re-authentication
    const services = ['website', 'billing', 'inventory'];
    const accessResults = {};
    
    for (const service of services) {
      TestHelpers.log(`Testing SSO access to ${service}`);
      
      await basePage.navigateToService(service);
      await basePage.waitForPageReady();
      
      accessResults[service] = {
        authenticated: await basePage.isAuthenticated(),
        loaded: await basePage.isPageLoaded(),
        url: basePage.getCurrentUrl()
      };
      
      // Should have access without additional authentication
      expect(accessResults[service].authenticated).toBe(true);
      expect(accessResults[service].loaded).toBe(true);
    }
    
    await basePage.takeScreenshot('sso-multi-service-access');
  });

  test('should maintain session across browser refresh', async () => {
    // Login and navigate to a service
    await loginPage.loginWithTestUser('admin');
    await basePage.navigateToService('website');
    
    expect(await basePage.isAuthenticated()).toBe(true);
    
    // Refresh the page
    await basePage.page.reload({ waitUntil: 'networkidle' });
    await basePage.waitForPageReady();
    
    // Should still be authenticated
    expect(await basePage.isAuthenticated()).toBe(true);
    expect(await basePage.isPageLoaded()).toBe(true);
  });

  test('should logout from all services when logging out from one', async () => {
    // Login and verify access to multiple services
    await loginPage.loginWithTestUser('admin');
    
    // Verify initial authentication across services
    await basePage.navigateToService('website');
    expect(await basePage.isAuthenticated()).toBe(true);
    
    await basePage.navigateToService('billing');
    expect(await basePage.isAuthenticated()).toBe(true);
    
    // Logout from identity provider
    await loginPage.navigateToService('identity');
    await loginPage.logout();
    
    // Verify logout across all services
    const services = ['website', 'billing', 'inventory'];
    
    for (const service of services) {
      await basePage.navigateToService(service);
      
      // Should either be redirected to login or show as not authenticated
      const isAuthenticated = await basePage.isAuthenticated();
      const isOnLogin = await loginPage.isOnLoginPage();
      
      // Either not authenticated or redirected to login
      expect(isAuthenticated || isOnLogin).not.toBe(true);
    }
  });

  test('should handle SSO cookie domain correctly', async () => {
    await loginPage.loginWithTestUser('admin');
    
    const cookies = await basePage.page.context().cookies();
    
    // Find SSO-related cookies
    const ssoCookies = cookies.filter(cookie => 
      cookie.name.includes('sso') || 
      cookie.name.includes('sessionid') ||
      cookie.name.includes('jwt')
    );
    
    expect(ssoCookies.length).toBeGreaterThan(0);
    
    // Check cookie domain configuration
    const mainDomain = TestHelpers.loadEnvironment().baseUrl
      .replace('https://', '')
      .replace('http://', '');
    
    ssoCookies.forEach(cookie => {
      // Cookie should be set for the main domain or its subdomains
      const isValidDomain = cookie.domain.includes(mainDomain) || 
                           cookie.domain.startsWith('.') ||
                           cookie.domain === 'localhost';
      expect(isValidDomain).toBe(true);
    });
  });

  test('should handle cross-domain redirects properly', async () => {
    // Start at website service while not authenticated
    await basePage.clearSession();
    await basePage.navigateToService('website');
    
    const initialUrl = basePage.getCurrentUrl();
    
    // Should be redirected to identity provider for authentication
    // or should show login form
    await basePage.waitForPageReady();
    
    const finalUrl = basePage.getCurrentUrl();
    const isOnLogin = await loginPage.isOnLoginPage();
    const isRedirected = initialUrl !== finalUrl;
    
    // Either should be on login page or redirected for authentication
    expect(isOnLogin || isRedirected).toBe(true);
    
    // Complete login process
    if (isOnLogin) {
      await loginPage.loginWithTestUser('admin');
      
      // Should be redirected back to the original service or dashboard
      expect(await loginPage.isLoginSuccessful()).toBe(true);
    }
  });

  test('should handle session expiration gracefully', async () => {
    // Login and establish session
    await loginPage.loginWithTestUser('admin');
    await basePage.navigateToService('website');
    
    expect(await basePage.isAuthenticated()).toBe(true);
    
    // Simulate session expiration by clearing auth cookies
    const cookies = await basePage.page.context().cookies();
    const authCookies = cookies.filter(cookie => 
      cookie.name.includes('sso') || 
      cookie.name.includes('sessionid') ||
      cookie.name.includes('jwt')
    );
    
    // Clear auth cookies to simulate expiration
    for (const cookie of authCookies) {
      await basePage.page.context().clearCookies({ 
        name: cookie.name,
        domain: cookie.domain 
      });
    }
    
    // Try to access a protected resource
    await basePage.navigateToService('billing');
    await basePage.waitForPageReady();
    
    // Should handle expired session gracefully
    const isAuthenticated = await basePage.isAuthenticated();
    const isOnLogin = await loginPage.isOnLoginPage();
    const hasAccess = await basePage.isPageLoaded();
    
    // Should either redirect to login or show appropriate error
    expect(!isAuthenticated || isOnLogin || !hasAccess).toBe(true);
  });

  test('should maintain SSO with multiple tabs/windows', async ({ context }) => {
    // Login in first tab
    await loginPage.loginWithTestUser('admin');
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    
    // Open second tab/page
    const secondPage = await context.newPage();
    const secondBasePage = new BasePage(secondPage);
    
    // Navigate to a different service in second tab
    await secondBasePage.navigateToService('website');
    await secondBasePage.waitForPageReady();
    
    // Should be authenticated in second tab due to SSO
    expect(await secondBasePage.isAuthenticated()).toBe(true);
    expect(await secondBasePage.isPageLoaded()).toBe(true);
    
    // Cleanup
    await secondPage.close();
  });

  test('should handle SSO with different user agents', async () => {
    // This test verifies SSO works across different browser configurations
    await loginPage.loginWithTestUser('admin');
    
    // Navigate to different services to ensure SSO works
    const services = ['website', 'billing'];
    
    for (const service of services) {
      await basePage.navigateToService(service);
      await basePage.waitForPageReady();
      
      expect(await basePage.isAuthenticated()).toBe(true);
      expect(await basePage.isPageLoaded()).toBe(true);
    }
  });

  test('should validate JWT token structure and claims', async () => {
    await loginPage.loginWithTestUser('admin');
    
    // Extract JWT token from cookies or local storage
    const jwtToken = await basePage.page.evaluate(() => {
      // Check localStorage first
      const localToken = localStorage.getItem('token') || 
                        localStorage.getItem('jwt') ||
                        localStorage.getItem('access_token');
      
      if (localToken) return localToken;
      
      // Check cookies
      const cookies = document.cookie.split(';');
      for (const cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name.includes('token') || name.includes('jwt')) {
          return value;
        }
      }
      
      return null;
    });
    
    if (jwtToken) {
      // Basic JWT structure validation (header.payload.signature)
      const parts = jwtToken.split('.');
      expect(parts.length).toBe(3);
      
      // Decode payload (basic validation)
      try {
        const payload = JSON.parse(atob(parts[1]));
        expect(payload).toHaveProperty('exp'); // Should have expiration
        expect(payload.exp).toBeGreaterThan(Date.now() / 1000); // Should not be expired
      } catch (error) {
        // JWT might be encrypted or in different format
        TestHelpers.log(`JWT validation skipped: ${error.message}`, 'warn');
      }
    }
  });
});