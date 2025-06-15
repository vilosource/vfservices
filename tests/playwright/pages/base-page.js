const TestHelpers = require('../utils/helpers');

class BasePage {
  constructor(page, environment = 'development') {
    this.page = page;
    this.environment = environment;
    this.env = TestHelpers.loadEnvironment(environment);
    this.timeout = 10000;
  }

  /**
   * Navigate to a specific service
   * @param {string} service - Service name (identity, website, billing, inventory)
   */
  async navigateToService(service) {
    const url = TestHelpers.getServiceUrl(service, this.environment);
    TestHelpers.log(`Navigating to ${service}: ${url}`);
    
    await this.page.goto(url, { 
      waitUntil: 'networkidle',
      timeout: this.timeout 
    });
    
    await this.waitForTraefikRoute();
  }

  /**
   * Wait for Traefik routing to complete
   */
  async waitForTraefikRoute() {
    await TestHelpers.waitForNetworkIdle(this.page, this.timeout);
    
    // Additional wait for any dynamic content to load
    await this.page.waitForTimeout(500);
  }

  /**
   * Check if page has loaded successfully
   * @returns {boolean} True if page loaded successfully
   */
  async isPageLoaded() {
    try {
      // Wait for basic DOM elements to be present
      await this.page.waitForSelector('body', { timeout: 5000 });
      
      // Check if there are any error messages or error pages
      const errorElements = await this.page.$$('[class*="error"], [id*="error"], .alert-danger');
      return errorElements.length === 0;
    } catch (error) {
      TestHelpers.log(`Page load check failed: ${error.message}`, 'warn');
      return false;
    }
  }

  /**
   * Get current URL
   * @returns {string} Current page URL
   */
  getCurrentUrl() {
    return this.page.url();
  }

  /**
   * Check if current page is the expected service
   * @param {string} expectedService - Expected service name
   * @returns {boolean} True if on expected service
   */
  isOnService(expectedService) {
    const currentUrl = this.getCurrentUrl();
    const expectedUrl = TestHelpers.getServiceUrl(expectedService, this.environment);
    
    // Extract domain from URLs for comparison
    const currentDomain = new URL(currentUrl).hostname;
    const expectedDomain = new URL(expectedUrl).hostname;
    
    return currentDomain === expectedDomain;
  }

  /**
   * Wait for element to be visible and clickable
   * @param {string} selector - Element selector
   * @param {number} timeout - Timeout in milliseconds
   */
  async waitForElement(selector, timeout = this.timeout) {
    await TestHelpers.waitForStableElement(this.page, selector, timeout);
  }

  /**
   * Click element with retry logic
   * @param {string} selector - Element selector
   * @param {Object} options - Click options
   */
  async click(selector, options = {}) {
    await this.waitForElement(selector);
    await this.page.click(selector, options);
    
    // Wait for any navigation or dynamic updates
    await this.page.waitForTimeout(100);
  }

  /**
   * Fill input field
   * @param {string} selector - Input selector
   * @param {string} value - Value to fill
   */
  async fill(selector, value) {
    await this.waitForElement(selector);
    await this.page.fill(selector, value);
  }

  /**
   * Get text content of element
   * @param {string} selector - Element selector
   * @returns {string} Text content
   */
  async getText(selector) {
    await this.waitForElement(selector);
    return await this.page.textContent(selector);
  }

  /**
   * Check if element is visible
   * @param {string} selector - Element selector
   * @returns {boolean} True if element is visible
   */
  async isVisible(selector) {
    try {
      await this.page.waitForSelector(selector, { state: 'visible', timeout: 2000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Check if element exists in DOM
   * @param {string} selector - Element selector
   * @returns {boolean} True if element exists
   */
  async exists(selector) {
    try {
      const element = await this.page.$(selector);
      return element !== null;
    } catch {
      return false;
    }
  }

  /**
   * Wait for navigation to complete
   * @param {Function} action - Action that triggers navigation
   */
  async waitForNavigation(action) {
    await Promise.all([
      this.page.waitForNavigation({ waitUntil: 'networkidle' }),
      action()
    ]);
    
    await this.waitForTraefikRoute();
  }

  /**
   * Take screenshot of current page
   * @param {string} name - Screenshot name
   */
  async takeScreenshot(name) {
    return await TestHelpers.takeScreenshot(this.page, name);
  }

  /**
   * Scroll element into view
   * @param {string} selector - Element selector
   */
  async scrollIntoView(selector) {
    await this.waitForElement(selector);
    await this.page.locator(selector).scrollIntoViewIfNeeded();
  }

  /**
   * Check for JavaScript errors on the page
   * @returns {Array} Array of JavaScript errors
   */
  async getJavaScriptErrors() {
    const errors = [];
    
    this.page.on('pageerror', error => {
      errors.push({
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });
    });
    
    return errors;
  }

  /**
   * Check if user is authenticated (has authentication cookies/tokens)
   * @returns {boolean} True if user appears to be authenticated
   */
  async isAuthenticated() {
    const cookies = await this.page.context().cookies();
    
    // Check for SSO cookie or JWT token
    const authCookies = cookies.filter(cookie => 
      cookie.name.includes('sso') || 
      cookie.name.includes('token') || 
      cookie.name.includes('jwt') ||
      cookie.name.includes('sessionid')
    );
    
    return authCookies.length > 0;
  }

  /**
   * Clear all cookies and local storage
   */
  async clearSession() {
    await this.page.context().clearCookies();
    await this.page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
  }

  /**
   * Get page title
   * @returns {string} Page title
   */
  async getTitle() {
    return await this.page.title();
  }

  /**
   * Wait for page to be ready for interaction
   */
  async waitForPageReady() {
    await this.page.waitForLoadState('domcontentloaded');
    await this.page.waitForLoadState('networkidle');
    
    // Wait for any loading spinners to disappear
    try {
      await this.page.waitForSelector('[class*="loading"], [class*="spinner"]', { 
        state: 'hidden', 
        timeout: 5000 
      });
    } catch {
      // Loading indicators might not be present, continue
    }
  }
}

module.exports = BasePage;