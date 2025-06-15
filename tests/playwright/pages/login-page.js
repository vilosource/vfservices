const BasePage = require('./base-page');
const TestHelpers = require('../utils/helpers');

class LoginPage extends BasePage {
  constructor(page, environment = 'development') {
    super(page, environment);
    
    // Selectors for login form elements
    this.selectors = {
      usernameInput: '#id_username, [name="username"], input[type="text"]',
      passwordInput: '#id_password, [name="password"], input[type="password"]',
      loginButton: 'button[type="submit"], input[type="submit"], .btn-login',
      errorMessage: '.alert-danger, .error-message, .invalid-feedback',
      loginForm: 'form, .login-form',
      logoutLink: 'a[href*="logout"], .logout-link',
      dashboardLink: 'a[href*="dashboard"], .dashboard-link'
    };
  }

  /**
   * Navigate to login page
   */
  async goto() {
    await this.navigateToService('identity');
    
    // Check if already on login page or if we need to navigate to it
    const isLoginPage = await this.isOnLoginPage();
    if (!isLoginPage) {
      // Try to find a login link
      const loginLink = await this.page.$('a[href*="login"], .login-link');
      if (loginLink) {
        await this.click('a[href*="login"], .login-link');
      }
    }
    
    await this.waitForPageReady();
  }

  /**
   * Check if currently on login page
   * @returns {boolean} True if on login page
   */
  async isOnLoginPage() {
    const hasLoginForm = await this.exists(this.selectors.loginForm);
    const hasUsernameField = await this.exists(this.selectors.usernameInput);
    const hasPasswordField = await this.exists(this.selectors.passwordInput);
    
    return hasLoginForm && hasUsernameField && hasPasswordField;
  }

  /**
   * Perform login with credentials
   * @param {string} username - Username
   * @param {string} password - Password
   */
  async login(username, password) {
    TestHelpers.log(`Attempting login with username: ${username}`);
    
    // Ensure we're on the login page
    await this.goto();
    
    // Wait for login form to be ready
    await this.waitForElement(this.selectors.usernameInput);
    await this.waitForElement(this.selectors.passwordInput);
    
    // Clear any existing values and fill credentials
    await this.page.fill(this.selectors.usernameInput, '');
    await this.page.fill(this.selectors.passwordInput, '');
    
    await this.fill(this.selectors.usernameInput, username);
    await this.fill(this.selectors.passwordInput, password);
    
    // Submit the form
    await this.waitForNavigation(async () => {
      await this.click(this.selectors.loginButton);
    });
    
    // Wait for post-login processing
    await this.waitForTraefikRoute();
    
    TestHelpers.log('Login form submitted, checking authentication status');
  }

  /**
   * Login with test user credentials
   * @param {string} userType - Type of user (admin, user, etc.)
   */
  async loginWithTestUser(userType = 'admin') {
    const testUser = TestHelpers.getTestUser(userType, this.environment);
    if (!testUser) {
      throw new Error(`No test user found for type: ${userType}`);
    }
    
    await this.login(testUser.username, testUser.password);
  }

  /**
   * Check if login was successful
   * @returns {boolean} True if login was successful
   */
  async isLoginSuccessful() {
    // Wait a moment for any redirects to complete
    await this.page.waitForTimeout(1000);
    
    // Check multiple indicators of successful login
    const notOnLoginPage = !(await this.isOnLoginPage());
    const hasAuthCookies = await this.isAuthenticated();
    const hasLogoutOption = await this.isVisible(this.selectors.logoutLink);
    
    // Check if we were redirected away from login page
    const currentUrl = this.getCurrentUrl();
    const isRedirected = !currentUrl.includes('/login') && !currentUrl.includes('/auth');
    
    const success = notOnLoginPage && (hasAuthCookies || hasLogoutOption || isRedirected);
    
    TestHelpers.log(`Login success check: notOnLoginPage=${notOnLoginPage}, hasAuthCookies=${hasAuthCookies}, hasLogoutOption=${hasLogoutOption}, isRedirected=${isRedirected}, overall=${success}`);
    
    return success;
  }

  /**
   * Check if login failed (error message present)
   * @returns {boolean} True if login failed
   */
  async isLoginFailed() {
    const hasErrorMessage = await this.isVisible(this.selectors.errorMessage);
    const stillOnLoginPage = await this.isOnLoginPage();
    
    return hasErrorMessage || stillOnLoginPage;
  }

  /**
   * Get login error message
   * @returns {string} Error message text
   */
  async getErrorMessage() {
    if (await this.isVisible(this.selectors.errorMessage)) {
      return await this.getText(this.selectors.errorMessage);
    }
    return '';
  }

  /**
   * Perform logout
   */
  async logout() {
    TestHelpers.log('Attempting logout');
    
    // Try to find and click logout link
    if (await this.isVisible(this.selectors.logoutLink)) {
      await this.waitForNavigation(async () => {
        await this.click(this.selectors.logoutLink);
      });
    } else {
      // If no logout link, try navigating to logout URL
      const logoutUrl = `${TestHelpers.getServiceUrl('identity', this.environment)}/logout/`;
      await this.page.goto(logoutUrl, { waitUntil: 'networkidle' });
    }
    
    await this.waitForTraefikRoute();
    TestHelpers.log('Logout completed');
  }

  /**
   * Check if user is logged out
   * @returns {boolean} True if user is logged out
   */
  async isLoggedOut() {
    const notAuthenticated = !(await this.isAuthenticated());
    const noLogoutLink = !(await this.isVisible(this.selectors.logoutLink));
    
    return notAuthenticated && noLogoutLink;
  }

  /**
   * Verify SSO cookie is set across domains
   * @returns {boolean} True if SSO cookie is present
   */
  async verifySSOCookie() {
    const cookies = await this.page.context().cookies();
    const ssoCookie = cookies.find(cookie => 
      cookie.name.includes('sso') || 
      cookie.domain.includes(this.env.baseUrl.replace('https://', '').replace('http://', ''))
    );
    
    const hasSSO = !!ssoCookie;
    TestHelpers.log(`SSO cookie verification: ${hasSSO ? 'found' : 'not found'}`);
    
    return hasSSO;
  }

  /**
   * Test cross-domain authentication by navigating to different services
   * @param {Array} services - List of services to test
   * @returns {Object} Results of cross-domain auth test
   */
  async testCrossDomainAuth(services = ['website', 'billing', 'inventory']) {
    const results = {};
    
    for (const service of services) {
      TestHelpers.log(`Testing cross-domain auth for service: ${service}`);
      
      try {
        await this.navigateToService(service);
        await this.waitForPageReady();
        
        const isAuth = await this.isAuthenticated();
        const hasAccess = await this.isPageLoaded();
        
        results[service] = {
          authenticated: isAuth,
          hasAccess: hasAccess,
          url: this.getCurrentUrl()
        };
        
        TestHelpers.log(`${service}: authenticated=${isAuth}, hasAccess=${hasAccess}`);
      } catch (error) {
        results[service] = {
          authenticated: false,
          hasAccess: false,
          error: error.message
        };
        TestHelpers.log(`${service}: error - ${error.message}`, 'error');
      }
    }
    
    return results;
  }

  /**
   * Clear all authentication data
   */
  async clearAuth() {
    await this.clearSession();
    TestHelpers.log('Authentication data cleared');
  }

  /**
   * Wait for login form to be ready for interaction
   */
  async waitForLoginForm() {
    await this.waitForElement(this.selectors.loginForm);
    await this.waitForElement(this.selectors.usernameInput);
    await this.waitForElement(this.selectors.passwordInput);
    await this.waitForElement(this.selectors.loginButton);
  }
}

module.exports = LoginPage;