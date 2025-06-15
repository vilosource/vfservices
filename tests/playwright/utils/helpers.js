const fs = require('fs');
const path = require('path');

class TestHelpers {
  /**
   * Load test environment configuration
   * @param {string} environment - Environment name (development, staging, production)
   * @returns {Object} Environment configuration
   */
  static loadEnvironment(environment = 'development') {
    const configPath = path.join(__dirname, '../config/test-environments.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return config.environments[environment];
  }

  /**
   * Get service URL for the current environment
   * @param {string} service - Service name (identity, website, billing, inventory)
   * @param {string} environment - Environment name
   * @returns {string} Service URL
   */
  static getServiceUrl(service, environment = 'development') {
    const env = this.loadEnvironment(environment);
    return env.services[service] || env.baseUrl;
  }

  /**
   * Get test user credentials
   * @param {string} userType - User type (admin, user, readonly)
   * @param {string} environment - Environment name
   * @returns {Object} User credentials
   */
  static getTestUser(userType = 'admin', environment = 'development') {
    const env = this.loadEnvironment(environment);
    return env.testUsers[userType];
  }

  /**
   * Wait for network idle state
   * @param {Page} page - Playwright page object
   * @param {number} timeout - Timeout in milliseconds
   */
  static async waitForNetworkIdle(page, timeout = 10000) {
    await page.waitForLoadState('networkidle', { timeout });
  }

  /**
   * Take screenshot with timestamp
   * @param {Page} page - Playwright page object
   * @param {string} testName - Test name for filename
   */
  static async takeScreenshot(page, testName) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const filename = `${testName}-${timestamp}.png`;
    const screenshotPath = path.join(__dirname, '../../test-results/screenshots', filename);
    
    // Ensure directory exists
    const dir = path.dirname(screenshotPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    await page.screenshot({ path: screenshotPath, fullPage: true });
    return screenshotPath;
  }

  /**
   * Generate random test data
   * @param {string} type - Data type (email, username, password)
   * @returns {string} Generated data
   */
  static generateTestData(type) {
    const timestamp = Date.now();
    
    switch (type) {
      case 'email':
        return `test-${timestamp}@example.com`;
      case 'username':
        return `testuser-${timestamp}`;
      case 'password':
        return `TestPass${timestamp}!`;
      default:
        return `test-data-${timestamp}`;
    }
  }

  /**
   * Wait for element to be visible and stable
   * @param {Page} page - Playwright page object
   * @param {string} selector - Element selector
   * @param {number} timeout - Timeout in milliseconds
   */
  static async waitForStableElement(page, selector, timeout = 5000) {
    await page.waitForSelector(selector, { state: 'visible', timeout });
    await page.waitForTimeout(100); // Small delay for animations
  }

  /**
   * Check if running in CI environment
   * @returns {boolean} True if running in CI
   */
  static isCI() {
    return !!process.env.CI;
  }

  /**
   * Log test step
   * @param {string} step - Step description
   * @param {string} level - Log level (info, warn, error)
   */
  static log(step, level = 'info') {
    const timestamp = new Date().toISOString();
    const prefix = level === 'error' ? '❌' : level === 'warn' ? '⚠️' : '✅';
    console.log(`${prefix} [${timestamp}] ${step}`);
  }

  /**
   * Retry operation with exponential backoff
   * @param {Function} operation - Operation to retry
   * @param {number} maxRetries - Maximum number of retries
   * @param {number} baseDelay - Base delay between retries in ms
   */
  static async retry(operation, maxRetries = 3, baseDelay = 1000) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await operation();
      } catch (error) {
        if (attempt === maxRetries) {
          throw error;
        }
        
        const delay = baseDelay * Math.pow(2, attempt - 1);
        this.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`, 'warn');
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
}

module.exports = TestHelpers;