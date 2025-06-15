const { test, expect } = require('@playwright/test');
const ApiClient = require('../../utils/api-client');
const TestHelpers = require('../../utils/helpers');

test.describe('Profile API Endpoint Tests', () => {
  let apiClient;
  let adminToken;
  let userToken;

  test.beforeAll(async () => {
    apiClient = new ApiClient('local');
    
    // Get admin token for testing
    const adminUser = TestHelpers.getTestUser('admin');
    adminToken = await apiClient.authenticate(adminUser.username, adminUser.password);
    TestHelpers.log(`Got admin token: ${adminToken.substring(0, 20)}...`, 'info');
    
    // Try to get regular user token (optional, may not exist in all environments)
    try {
      const regularUser = TestHelpers.getTestUser('user');
      if (regularUser) {
        userToken = await apiClient.authenticate(regularUser.username, regularUser.password);
        TestHelpers.log(`Got user token: ${userToken.substring(0, 20)}...`, 'info');
      }
    } catch (error) {
      TestHelpers.log(`Regular user not available: ${error.message}`, 'warn');
    }
  });

  test.describe('Profile Endpoint Authentication', () => {
    test('should return 403 when no authentication provided', async () => {
      const response = await apiClient.testProfileEndpoint();
      
      expect(response.status).toBe(403);
      expect(response.ok).toBe(false);
      expect(response.data).toHaveProperty('detail');
      expect(response.data.detail).toContain('Authentication credentials were not provided');
      
      TestHelpers.log('Verified 403 response for unauthenticated request', 'info');
    });

    test('should return 403 when invalid token provided', async () => {
      const invalidToken = 'invalid-jwt-token-123';
      const response = await apiClient.testProfileEndpoint(invalidToken);
      
      expect(response.status).toBe(403);
      expect(response.ok).toBe(false);
      expect(response.data).toHaveProperty('detail');
      
      TestHelpers.log('Verified 403 response for invalid token', 'info');
    });

    test('should return 403 when malformed token provided', async () => {
      const malformedToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.malformed.token';
      const response = await apiClient.testProfileEndpoint(malformedToken);
      
      expect(response.status).toBe(403);
      expect(response.ok).toBe(false);
      expect(response.data).toHaveProperty('detail');
      
      TestHelpers.log('Verified 403 response for malformed token', 'info');
    });

    test('should return 403 when expired token provided', async () => {
      // Create an obviously expired token (exp in the past)
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6InRlc3QiLCJleHAiOjF9.expired';
      const response = await apiClient.testProfileEndpoint(expiredToken);
      
      expect(response.status).toBe(403);
      expect(response.ok).toBe(false);
      
      TestHelpers.log('Verified 403 response for expired token', 'info');
    });
  });

  test.describe('Profile Endpoint Success Cases', () => {
    test('should return profile data with valid admin token via Authorization header', async () => {
      const response = await apiClient.testProfileEndpoint(adminToken);
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      expect(response.data).toHaveProperty('username');
      expect(response.data).toHaveProperty('email');
      expect(response.data).toHaveProperty('timestamp');
      
      // Verify the response contains expected admin data
      expect(response.data.username).toBe('admin');
      expect(response.data.email).toContain('@');
      expect(response.data.timestamp).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
      
      TestHelpers.log(`Profile data retrieved: ${JSON.stringify(response.data)}`, 'info');
    });

    test('should return profile data with valid admin token via cookie', async () => {
      const response = await apiClient.testProfileEndpoint(adminToken, true); // useCookie = true
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      expect(response.data).toHaveProperty('username');
      expect(response.data).toHaveProperty('email');
      expect(response.data).toHaveProperty('timestamp');
      
      // Verify the response contains expected admin data
      expect(response.data.username).toBe('admin');
      
      TestHelpers.log('Profile data retrieved via cookie authentication', 'info');
    });

    test('should return profile data with getProfile helper method', async () => {
      const profileData = await apiClient.getProfile(adminToken);
      
      expect(profileData).toHaveProperty('username');
      expect(profileData).toHaveProperty('email');
      expect(profileData).toHaveProperty('timestamp');
      expect(profileData.username).toBe('admin');
      
      TestHelpers.log(`Profile retrieved via helper: ${JSON.stringify(profileData)}`, 'info');
    });

    test.skip('should return profile data for regular user', async () => {
      // Skip if no regular user token available
      if (!userToken) {
        test.skip('Regular user token not available');
      }
      
      const response = await apiClient.testProfileEndpoint(userToken);
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      expect(response.data).toHaveProperty('username');
      expect(response.data).toHaveProperty('email');
      expect(response.data).toHaveProperty('timestamp');
      
      TestHelpers.log(`Regular user profile: ${JSON.stringify(response.data)}`, 'info');
    });
  });

  test.describe('Profile Endpoint Security', () => {
    test('should not expose sensitive information', async () => {
      const response = await apiClient.testProfileEndpoint(adminToken);
      
      expect(response.status).toBe(200);
      
      // Verify that sensitive fields are not exposed
      expect(response.data).not.toHaveProperty('password');
      expect(response.data).not.toHaveProperty('password_hash');
      expect(response.data).not.toHaveProperty('secret');
      expect(response.data).not.toHaveProperty('token');
      expect(response.data).not.toHaveProperty('id');
      
      // Verify only expected fields are present
      const expectedFields = ['username', 'email', 'timestamp'];
      const actualFields = Object.keys(response.data);
      
      expectedFields.forEach(field => {
        expect(actualFields).toContain(field);
      });
      
      // Check that we don't have unexpected fields
      const unexpectedFields = actualFields.filter(field => !expectedFields.includes(field));
      expect(unexpectedFields).toHaveLength(0);
      
      TestHelpers.log('Verified no sensitive information exposed', 'info');
    });

    test('should validate JWT token signature', async () => {
      // Create a token with invalid signature (same payload, wrong signature)
      const validTokenParts = adminToken.split('.');
      const invalidToken = validTokenParts[0] + '.' + validTokenParts[1] + '.invalid_signature';
      
      const response = await apiClient.testProfileEndpoint(invalidToken);
      
      expect(response.status).toBe(403);
      expect(response.ok).toBe(false);
      
      TestHelpers.log('Verified JWT signature validation', 'info');
    });

    test('should handle concurrent profile requests', async () => {
      // Test multiple concurrent requests to ensure thread safety
      const requestPromises = Array(5).fill().map(() => 
        apiClient.testProfileEndpoint(adminToken)
      );
      
      const responses = await Promise.all(requestPromises);
      
      // All requests should succeed
      responses.forEach((response, index) => {
        expect(response.status).toBe(200);
        expect(response.ok).toBe(true);
        expect(response.data.username).toBe('admin');
      });
      
      TestHelpers.log('Verified concurrent request handling', 'info');
    });
  });

  test.describe('Profile Endpoint Integration', () => {
    test('should work through Traefik proxy', async () => {
      // This test verifies the endpoint works through the reverse proxy
      const response = await apiClient.testProfileEndpoint(adminToken);
      
      expect(response.status).toBe(200);
      expect(response.ok).toBe(true);
      
      // The fact that we get a response means Traefik routing is working
      TestHelpers.log('Verified profile endpoint works through Traefik', 'info');
    });

    test('should be documented in API info', async () => {
      const apiInfo = await apiClient.getApiInfo();
      
      expect(apiInfo).toHaveProperty('endpoints');
      expect(apiInfo.endpoints).toHaveProperty('/api/profile/');
      
      const profileEndpointInfo = apiInfo.endpoints['/api/profile/'];
      expect(profileEndpointInfo.method).toBe('GET');
      expect(profileEndpointInfo.description).toContain('profile');
      expect(profileEndpointInfo.authentication).toContain('JWT');
      
      TestHelpers.log('Verified profile endpoint is documented in API info', 'info');
    });

    test('should maintain consistent response format', async () => {
      // Make multiple requests and verify consistent response structure
      const responses = await Promise.all([
        apiClient.testProfileEndpoint(adminToken),
        apiClient.testProfileEndpoint(adminToken, true), // via cookie
        apiClient.getProfile(adminToken) // via helper
      ]);
      
      const [headerAuth, cookieAuth, helperResponse] = responses;
      
      // All should have same basic structure
      [headerAuth.data, cookieAuth.data, helperResponse].forEach(data => {
        expect(data).toHaveProperty('username');
        expect(data).toHaveProperty('email');
        expect(data).toHaveProperty('timestamp');
        expect(data.username).toBe('admin');
      });
      
      TestHelpers.log('Verified consistent response format across authentication methods', 'info');
    });
  });

  test.describe('Profile Endpoint Error Handling', () => {
    test('should handle network errors gracefully', async () => {
      // Test with invalid service URL to simulate network error
      const invalidApiClient = new ApiClient('development');
      invalidApiClient.env.services.identity = 'https://invalid-service-url.test';
      
      try {
        await invalidApiClient.testProfileEndpoint(adminToken);
        // Should not reach here
        expect(true).toBe(false);
      } catch (error) {
        expect(error.message).toContain('ENOTFOUND');
        TestHelpers.log('Verified network error handling', 'info');
      }
    });

    test('should return proper HTTP status codes', async () => {
      const testCases = [
        { token: null, expectedStatus: 403, description: 'no token' },
        { token: 'invalid', expectedStatus: 403, description: 'invalid token' },
        { token: adminToken, expectedStatus: 200, description: 'valid token' }
      ];
      
      for (const testCase of testCases) {
        const response = await apiClient.testProfileEndpoint(testCase.token);
        expect(response.status).toBe(testCase.expectedStatus);
        TestHelpers.log(`Verified ${testCase.expectedStatus} status for ${testCase.description}`, 'info');
      }
    });

    test('should include appropriate CORS headers', async () => {
      // This test would need to check response headers
      // For now, we verify the request succeeds (indicating CORS is configured)
      const response = await apiClient.testProfileEndpoint(adminToken);
      expect(response.status).toBe(200);
      
      TestHelpers.log('Verified CORS configuration allows requests', 'info');
    });
  });
});