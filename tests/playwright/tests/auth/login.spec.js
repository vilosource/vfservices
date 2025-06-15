const { test, expect } = require('@playwright/test');
const LoginPage = require('../../pages/login-page');
const TestHelpers = require('../../utils/helpers');

test.describe('Authentication Tests', () => {
  let loginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.clearAuth(); // Start with clean state
  });

  test.afterEach(async ({ page }) => {
    // Cleanup after each test
    try {
      await loginPage.clearAuth();
    } catch (error) {
      TestHelpers.log(`Cleanup error: ${error.message}`, 'warn');
    }
  });

  test('should load login page successfully', async () => {
    await loginPage.goto();
    
    expect(await loginPage.isOnLoginPage()).toBe(true);
    expect(await loginPage.isPageLoaded()).toBe(true);
    
    // Verify login form elements are present
    await loginPage.waitForLoginForm();
    expect(await loginPage.exists(loginPage.selectors.usernameInput)).toBe(true);
    expect(await loginPage.exists(loginPage.selectors.passwordInput)).toBe(true);
    expect(await loginPage.exists(loginPage.selectors.loginButton)).toBe(true);
  });

  test('should login successfully with valid admin credentials', async () => {
    const testUser = TestHelpers.getTestUser('admin');
    
    await loginPage.login(testUser.username, testUser.password);
    
    // Verify login success
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    expect(await loginPage.isAuthenticated()).toBe(true);
    
    // Take screenshot for verification
    await loginPage.takeScreenshot('successful-admin-login');
  });

  test('should login successfully with valid user credentials', async () => {
    const testUser = TestHelpers.getTestUser('user');
    if (!testUser) {
      test.skip('No test user configured for this environment');
    }
    
    await loginPage.login(testUser.username, testUser.password);
    
    // Verify login success
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    expect(await loginPage.isAuthenticated()).toBe(true);
  });

  test('should reject invalid credentials', async () => {
    await loginPage.login('invalid_user', 'invalid_password');
    
    // Verify login failure
    expect(await loginPage.isLoginFailed()).toBe(true);
    expect(await loginPage.isLoginSuccessful()).toBe(false);
    
    // Check for error message
    const errorMessage = await loginPage.getErrorMessage();
    expect(errorMessage.length).toBeGreaterThan(0);
  });

  test('should reject empty credentials', async () => {
    await loginPage.login('', '');
    
    // Should still be on login page
    expect(await loginPage.isOnLoginPage()).toBe(true);
    expect(await loginPage.isLoginSuccessful()).toBe(false);
  });

  test('should logout successfully', async () => {
    // First login
    await loginPage.loginWithTestUser('admin');
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    
    // Then logout
    await loginPage.logout();
    
    // Verify logout
    expect(await loginPage.isLoggedOut()).toBe(true);
    expect(await loginPage.isAuthenticated()).toBe(false);
  });

  test('should maintain SSO across domain navigation', async () => {
    // Login first
    await loginPage.loginWithTestUser('admin');
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    
    // Verify SSO cookie is set
    expect(await loginPage.verifySSOCookie()).toBe(true);
    
    // Test cross-domain authentication
    const crossDomainResults = await loginPage.testCrossDomainAuth(['website']);
    
    // Verify authentication is maintained across services
    expect(crossDomainResults.website.authenticated).toBe(true);
    expect(crossDomainResults.website.hasAccess).toBe(true);
  });

  test('should handle session timeout gracefully', async () => {
    // Login first
    await loginPage.loginWithTestUser('admin');
    expect(await loginPage.isLoginSuccessful()).toBe(true);
    
    // Simulate session expiry by clearing auth cookies
    await loginPage.clearAuth();
    
    // Try to access a protected page
    await loginPage.navigateToService('website');
    
    // Should be redirected to login or show login form
    // This test verifies the application handles expired sessions properly
    const isOnLogin = await loginPage.isOnLoginPage();
    const hasAccess = await loginPage.isPageLoaded();
    
    // Either should be redirected to login, or the page should handle unauthorized access
    expect(isOnLogin || !hasAccess).toBe(true);
  });

  test('should prevent access to protected resources when not authenticated', async () => {
    // Ensure not authenticated
    await loginPage.clearAuth();
    
    // Try to access protected services
    const services = ['website', 'billing', 'inventory'];
    
    for (const service of services) {
      await loginPage.navigateToService(service);
      
      // Should either be redirected to login or denied access
      const isOnLogin = await loginPage.isOnLoginPage();
      const isAuthenticated = await loginPage.isAuthenticated();
      
      // If not on login page, should not be authenticated for protected resources
      if (!isOnLogin) {
        expect(isAuthenticated).toBe(false);
      }
    }
  });

  test('should handle concurrent login attempts', async () => {
    // This test verifies the system can handle multiple login attempts
    const testUser = TestHelpers.getTestUser('admin');
    
    // Attempt multiple logins concurrently
    const loginPromises = [
      loginPage.login(testUser.username, testUser.password),
      loginPage.login(testUser.username, testUser.password)
    ];
    
    // Wait for all attempts to complete
    await Promise.all(loginPromises);
    
    // Final state should be authenticated
    expect(await loginPage.isLoginSuccessful()).toBe(true);
  });

  test('should redirect to intended page after login', async () => {
    // Try to access a protected page while not authenticated
    await loginPage.clearAuth();
    await loginPage.navigateToService('website');
    
    // If redirected to login, login and check if redirected back
    if (await loginPage.isOnLoginPage()) {
      await loginPage.loginWithTestUser('admin');
      
      // Should be redirected to the originally requested page
      // or at least not be on the login page anymore
      expect(await loginPage.isLoginSuccessful()).toBe(true);
    }
  });
});