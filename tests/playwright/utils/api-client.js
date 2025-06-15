const { request } = require('@playwright/test');
const TestHelpers = require('./helpers');

class ApiClient {
  constructor(environment = 'development') {
    this.environment = environment;
    this.env = TestHelpers.loadEnvironment(environment);
  }

  /**
   * Create API request context
   * @param {string} service - Service name for Host header (optional)
   * @returns {APIRequestContext} Playwright API request context
   */
  async createContext(service = null) {
    const headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    };

    // Add Host header for local testing if hostHeaders are configured
    if (this.env.hostHeaders && service && this.env.hostHeaders[service]) {
      headers['Host'] = this.env.hostHeaders[service];
    }

    return await request.newContext({
      baseURL: this.env.baseUrl,
      ignoreHTTPSErrors: true,
      extraHTTPHeaders: headers
    });
  }

  /**
   * Authenticate user and return JWT token
   * @param {string} username - Username
   * @param {string} password - Password
   * @returns {string} JWT token
   */
  async authenticate(username, password) {
    const context = await this.createContext('identity');
    
    try {
      const response = await context.post(`${this.env.services.identity}/api/login/`, {
        data: {
          username,
          password
        }
      });

      if (!response.ok()) {
        throw new Error(`Authentication failed: ${response.status()}`);
      }

      const data = await response.json();
      return data.token || data.access_token;
    } finally {
      await context.dispose();
    }
  }

  /**
   * Get user profile information
   * @param {string} token - JWT token
   * @returns {Object} User profile data
   */
  async getProfile(token) {
    const context = await this.createContext('identity');
    
    try {
      const response = await context.get(`${this.env.services.identity}/api/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok()) {
        throw new Error(`Profile request failed: ${response.status()}`);
      }

      return await response.json();
    } finally {
      await context.dispose();
    }
  }

  /**
   * Test profile endpoint with various authentication scenarios
   * @param {string} token - JWT token (can be invalid/null for negative tests)
   * @param {boolean} useCookie - Whether to use cookie instead of Authorization header
   * @returns {Object} Response data and status
   */
  async testProfileEndpoint(token = null, useCookie = false) {
    const context = await this.createContext('identity');
    
    try {
      const options = {};
      
      if (token) {
        if (useCookie) {
          options.headers = {
            'Cookie': `jwt=${token}`
          };
        } else {
          options.headers = {
            'Authorization': `Bearer ${token}`
          };
        }
      }

      const response = await context.get(`${this.env.services.identity}/api/profile/`, options);
      
      let data = null;
      try {
        data = await response.json();
      } catch (e) {
        // Response might not be JSON for some error cases
        data = await response.text();
      }

      return {
        status: response.status(),
        ok: response.ok(),
        data: data
      };
    } finally {
      await context.dispose();
    }
  }

  /**
   * Get API information from identity service
   * @returns {Object} API information
   */
  async getApiInfo() {
    const context = await this.createContext('identity');
    
    try {
      const response = await context.get(`${this.env.services.identity}/api/`);
      
      if (!response.ok()) {
        throw new Error(`API info request failed: ${response.status()}`);
      }

      return await response.json();
    } finally {
      await context.dispose();
    }
  }

  /**
   * Make authenticated API request
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {string} token - JWT token
   * @param {Object} data - Request data
   * @returns {Response} API response
   */
  async makeAuthenticatedRequest(method, endpoint, token, data = null) {
    const context = await this.createContext();
    
    try {
      const options = {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      };

      if (data) {
        options.data = data;
      }

      return await context[method.toLowerCase()](endpoint, options);
    } finally {
      await context.dispose();
    }
  }

  /**
   * Health check for all services
   * @returns {Object} Health status of all services
   */
  async healthCheck() {
    const context = await this.createContext();
    const results = {};
    
    try {
      for (const [serviceName, serviceUrl] of Object.entries(this.env.services)) {
        try {
          const response = await context.get(`${serviceUrl}/health/`, {
            timeout: 5000
          });
          results[serviceName] = {
            status: response.status(),
            ok: response.ok(),
            url: serviceUrl
          };
        } catch (error) {
          results[serviceName] = {
            status: 'error',
            ok: false,
            url: serviceUrl,
            error: error.message
          };
        }
      }
    } finally {
      await context.dispose();
    }
    
    return results;
  }

  /**
   * Create test user via API
   * @param {Object} userData - User data
   * @param {string} adminToken - Admin JWT token
   * @returns {Object} Created user data
   */
  async createTestUser(userData, adminToken) {
    const context = await this.createContext();
    
    try {
      const response = await context.post(`${this.env.services.identity}/api/users/`, {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        },
        data: userData
      });

      if (!response.ok()) {
        throw new Error(`User creation failed: ${response.status()}`);
      }

      return await response.json();
    } finally {
      await context.dispose();
    }
  }

  /**
   * Delete test user via API
   * @param {string} userId - User ID
   * @param {string} adminToken - Admin JWT token
   */
  async deleteTestUser(userId, adminToken) {
    const context = await this.createContext();
    
    try {
      const response = await context.delete(`${this.env.services.identity}/api/users/${userId}/`, {
        headers: {
          'Authorization': `Bearer ${adminToken}`
        }
      });

      if (!response.ok()) {
        TestHelpers.log(`Warning: Failed to delete test user ${userId}: ${response.status()}`, 'warn');
      }
    } finally {
      await context.dispose();
    }
  }

  /**
   * Setup test data for a test suite
   * @param {string} testSuite - Test suite name
   * @param {string} adminToken - Admin JWT token
   * @returns {Object} Test data
   */
  async setupTestData(testSuite, adminToken) {
    const testData = {
      testSuite,
      createdAt: new Date().toISOString(),
      users: [],
      cleanup: []
    };

    // Create test users based on test suite needs
    switch (testSuite) {
      case 'auth':
        // Create a test user for authentication tests
        const testUser = await this.createTestUser({
          username: TestHelpers.generateTestData('username'),
          email: TestHelpers.generateTestData('email'),
          password: TestHelpers.generateTestData('password'),
          is_active: true
        }, adminToken);
        
        testData.users.push(testUser);
        testData.cleanup.push(() => this.deleteTestUser(testUser.id, adminToken));
        break;
      
      default:
        // Default test data setup
        break;
    }

    return testData;
  }

  /**
   * Cleanup test data
   * @param {Object} testData - Test data object with cleanup functions
   */
  async cleanupTestData(testData) {
    if (testData.cleanup) {
      for (const cleanupFn of testData.cleanup) {
        try {
          await cleanupFn();
        } catch (error) {
          TestHelpers.log(`Cleanup error: ${error.message}`, 'warn');
        }
      }
    }
  }
}

module.exports = ApiClient;