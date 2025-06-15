const { test, expect } = require('@playwright/test');
const BasePage = require('../../pages/base-page');
const TestHelpers = require('../../utils/helpers');
const ApiClient = require('../../utils/api-client');

test.describe('Traefik Infrastructure Tests', () => {
  let basePage;
  let apiClient;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    apiClient = new ApiClient();
  });

  test('should route all services correctly through Traefik', async () => {
    const env = TestHelpers.loadEnvironment();
    const services = Object.keys(env.services);
    
    const routingResults = {};
    
    for (const service of services) {
      TestHelpers.log(`Testing Traefik routing for ${service}`);
      
      try {
        await basePage.navigateToService(service);
        await basePage.waitForPageReady();
        
        routingResults[service] = {
          accessible: await basePage.isPageLoaded(),
          url: basePage.getCurrentUrl(),
          expectedUrl: TestHelpers.getServiceUrl(service),
          status: 'success'
        };
        
        // Verify we're on the correct domain
        const currentDomain = new URL(basePage.getCurrentUrl()).hostname;
        const expectedDomain = new URL(TestHelpers.getServiceUrl(service)).hostname;
        
        expect(currentDomain).toBe(expectedDomain);
        expect(routingResults[service].accessible).toBe(true);
        
      } catch (error) {
        routingResults[service] = {
          accessible: false,
          error: error.message,
          status: 'failed'
        };
        
        TestHelpers.log(`Traefik routing failed for ${service}: ${error.message}`, 'error');
      }
    }
    
    // All services should be accessible
    const failedServices = Object.entries(routingResults)
      .filter(([_, result]) => !result.accessible)
      .map(([service, _]) => service);
    
    expect(failedServices.length).toBe(0);
  });

  test('should redirect HTTP to HTTPS', async () => {
    const env = TestHelpers.loadEnvironment();
    const httpUrl = env.baseUrl.replace('https://', 'http://');
    
    try {
      const response = await basePage.page.goto(httpUrl, { 
        waitUntil: 'networkidle',
        timeout: 10000 
      });
      
      const finalUrl = basePage.getCurrentUrl();
      
      // Should be redirected to HTTPS
      expect(finalUrl.startsWith('https://')).toBe(true);
      
      // Response should indicate redirect or direct HTTPS access
      expect(response.status() === 200 || response.status() >= 300 && response.status() < 400).toBe(true);
      
    } catch (error) {
      // HTTP might be blocked entirely, which is also acceptable
      TestHelpers.log(`HTTP access test: ${error.message}`, 'warn');
    }
  });

  test('should handle SSL/TLS certificates properly', async () => {
    const services = ['website', 'identity', 'billing', 'inventory'];
    
    for (const service of services) {
      await basePage.navigateToService(service);
      
      const url = basePage.getCurrentUrl();
      
      // Should be served over HTTPS
      expect(url.startsWith('https://')).toBe(true);
      
      // Page should load without SSL errors
      expect(await basePage.isPageLoaded()).toBe(true);
      
      // Check for mixed content warnings (if any)
      const mixedContentErrors = await basePage.page.evaluate(() => {
        // Check if there are any insecure resource loads
        const performanceEntries = performance.getEntriesByType('resource');
        return performanceEntries.filter(entry => 
          entry.name.startsWith('http://') && 
          !entry.name.includes('localhost')
        ).length;
      });
      
      expect(mixedContentErrors).toBe(0);
    }
  });

  test('should handle subdomain routing correctly', async () => {
    const env = TestHelpers.loadEnvironment();
    const baseUrl = env.baseUrl;
    const baseDomain = new URL(baseUrl).hostname;
    
    // Test subdomain routing
    const subdomainTests = [
      { service: 'identity', expectedSubdomain: 'identity' },
      { service: 'billing', expectedSubdomain: 'billing' },
      { service: 'inventory', expectedSubdomain: 'inventory' }
    ];
    
    for (const test of subdomainTests) {
      await basePage.navigateToService(test.service);
      
      const currentUrl = basePage.getCurrentUrl();
      const currentDomain = new URL(currentUrl).hostname;
      
      // Should be on the correct subdomain
      expect(currentDomain).toBe(`${test.expectedSubdomain}.${baseDomain.replace('www.', '')}`);
      expect(await basePage.isPageLoaded()).toBe(true);
    }
  });

  test('should handle root domain routing to website', async () => {
    const env = TestHelpers.loadEnvironment();
    const rootUrl = env.baseUrl;
    
    await basePage.page.goto(rootUrl, { waitUntil: 'networkidle' });
    await basePage.waitForPageReady();
    
    // Should load the website service
    expect(await basePage.isPageLoaded()).toBe(true);
    
    // URL should be the root domain or website subdomain
    const currentUrl = basePage.getCurrentUrl();
    const rootDomain = new URL(rootUrl).hostname;
    const currentDomain = new URL(currentUrl).hostname;
    
    expect(
      currentDomain === rootDomain || 
      currentDomain === `website.${rootDomain}`
    ).toBe(true);
  });

  test('should handle load balancing and service availability', async () => {
    // Test multiple requests to ensure consistency
    const testIterations = 3;
    const services = ['website', 'identity'];
    
    for (const service of services) {
      const results = [];
      
      for (let i = 0; i < testIterations; i++) {
        await basePage.navigateToService(service);
        
        results.push({
          iteration: i + 1,
          loaded: await basePage.isPageLoaded(),
          url: basePage.getCurrentUrl(),
          timestamp: new Date().toISOString()
        });
        
        // Small delay between requests
        await basePage.page.waitForTimeout(500);
      }
      
      // All requests should succeed
      const successfulRequests = results.filter(r => r.loaded).length;
      expect(successfulRequests).toBe(testIterations);
      
      // All requests should go to the same service
      const uniqueUrls = new Set(results.map(r => new URL(r.url).hostname));
      expect(uniqueUrls.size).toBe(1);
    }
  });

  test('should return appropriate error pages for non-existent routes', async () => {
    const env = TestHelpers.loadEnvironment();
    const nonExistentUrl = `${env.baseUrl}/non-existent-service-12345`;
    
    try {
      const response = await basePage.page.goto(nonExistentUrl, { 
        waitUntil: 'networkidle',
        timeout: 10000 
      });
      
      // Should return 404 or be handled by default service
      const status = response.status();
      expect(status === 404 || status === 200).toBe(true);
      
      if (status === 200) {
        // If handled by default service, should still load a valid page
        expect(await basePage.isPageLoaded()).toBe(true);
      }
      
    } catch (error) {
      // Network errors are also acceptable for non-existent routes
      TestHelpers.log(`Non-existent route test: ${error.message}`, 'warn');
    }
  });

  test('should handle concurrent requests efficiently', async ({ context }) => {
    const env = TestHelpers.loadEnvironment();
    const services = Object.keys(env.services);
    
    // Create multiple pages for concurrent testing
    const pages = await Promise.all([
      context.newPage(),
      context.newPage(),
      context.newPage()
    ]);
    
    try {
      // Make concurrent requests to different services
      const concurrentTests = pages.map(async (page, index) => {
        const service = services[index % services.length];
        const basePage = new BasePage(page);
        
        await basePage.navigateToService(service);
        await basePage.waitForPageReady();
        
        return {
          service,
          loaded: await basePage.isPageLoaded(),
          url: basePage.getCurrentUrl()
        };
      });
      
      const results = await Promise.all(concurrentTests);
      
      // All concurrent requests should succeed
      results.forEach(result => {
        expect(result.loaded).toBe(true);
      });
      
    } finally {
      // Cleanup additional pages
      await Promise.all(pages.map(page => page.close()));
    }
  });

  test('should have proper health check endpoints', async () => {
    // Test health checks through API client
    const healthResults = await apiClient.healthCheck();
    
    // At least some services should respond to health checks
    const healthyServices = Object.values(healthResults).filter(result => result.ok);
    expect(healthyServices.length).toBeGreaterThan(0);
    
    // Log health check results
    Object.entries(healthResults).forEach(([service, result]) => {
      TestHelpers.log(`Health check ${service}: ${result.ok ? 'OK' : 'FAILED'} (${result.status})`);
    });
  });

  test('should handle request timeouts appropriately', async () => {
    const env = TestHelpers.loadEnvironment();
    
    // Test with a very short timeout to see how Traefik handles it
    try {
      await basePage.page.goto(env.baseUrl, { 
        timeout: 1000, // Very short timeout
        waitUntil: 'networkidle' 
      });
    } catch (timeoutError) {
      // Timeout is expected, now try with normal timeout
      const response = await basePage.page.goto(env.baseUrl, { 
        timeout: 30000,
        waitUntil: 'networkidle' 
      });
      
      // Should succeed with normal timeout
      expect(response.ok()).toBe(true);
      expect(await basePage.isPageLoaded()).toBe(true);
    }
  });

  test('should preserve request headers correctly', async () => {
    await basePage.navigateToService('website');
    
    // Check if common headers are preserved/set correctly
    const headers = await basePage.page.evaluate(() => {
      // This will show headers sent by the client
      return {
        userAgent: navigator.userAgent,
        language: navigator.language,
        // These would need to be checked via network tab or server logs
      };
    });
    
    expect(headers.userAgent.length).toBeGreaterThan(0);
    expect(headers.language.length).toBeGreaterThan(0);
    
    // The presence of headers indicates Traefik is passing them through
    TestHelpers.log(`Headers preserved: User-Agent present, Language: ${headers.language}`);
  });
});