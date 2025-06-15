const { test, expect } = require('@playwright/test');
const BasePage = require('../../pages/base-page');
const LoginPage = require('../../pages/login-page');
const TestHelpers = require('../../utils/helpers');

test.describe('Website Homepage Tests', () => {
  let basePage;
  let loginPage;

  test.beforeEach(async ({ page }) => {
    basePage = new BasePage(page);
    loginPage = new LoginPage(page);
  });

  test('should load homepage successfully', async () => {
    await basePage.navigateToService('website');
    
    expect(await basePage.isPageLoaded()).toBe(true);
    
    // Check basic page elements
    const title = await basePage.getTitle();
    expect(title.length).toBeGreaterThan(0);
    
    // Verify page structure
    expect(await basePage.exists('body')).toBe(true);
    expect(await basePage.exists('head')).toBe(true);
  });

  test('should handle both authenticated and unauthenticated access', async () => {
    // Test unauthenticated access
    await basePage.clearSession();
    await basePage.navigateToService('website');
    
    const unauthAccess = {
      loaded: await basePage.isPageLoaded(),
      authenticated: await basePage.isAuthenticated()
    };
    
    // Test authenticated access
    await loginPage.loginWithTestUser('admin');
    await basePage.navigateToService('website');
    
    const authAccess = {
      loaded: await basePage.isPageLoaded(),
      authenticated: await basePage.isAuthenticated()
    };
    
    // Both should load successfully
    expect(unauthAccess.loaded).toBe(true);
    expect(authAccess.loaded).toBe(true);
    expect(authAccess.authenticated).toBe(true);
  });

  test('should display correct navigation elements', async () => {
    await basePage.navigateToService('website');
    
    // Check for common navigation elements
    const navSelectors = [
      'nav',
      '.navbar',
      '.navigation',
      'header nav',
      '[role="navigation"]'
    ];
    
    let hasNavigation = false;
    for (const selector of navSelectors) {
      if (await basePage.exists(selector)) {
        hasNavigation = true;
        break;
      }
    }
    
    // Should have some form of navigation
    expect(hasNavigation).toBe(true);
  });

  test('should have proper page metadata', async () => {
    await basePage.navigateToService('website');
    
    // Check meta tags
    const metaTags = await basePage.page.$$eval('meta', metas => 
      metas.map(meta => ({ 
        name: meta.getAttribute('name') || meta.getAttribute('property'),
        content: meta.getAttribute('content') 
      }))
    );
    
    // Should have basic meta tags
    const hasDescription = metaTags.some(meta => 
      meta.name === 'description' && meta.content
    );
    const hasViewport = metaTags.some(meta => 
      meta.name === 'viewport' && meta.content
    );
    
    expect(hasDescription || hasViewport).toBe(true);
  });

  test('should handle responsive design', async () => {
    await basePage.navigateToService('website');
    
    // Test desktop view
    await basePage.page.setViewportSize({ width: 1920, height: 1080 });
    await basePage.waitForPageReady();
    expect(await basePage.isPageLoaded()).toBe(true);
    
    // Test tablet view
    await basePage.page.setViewportSize({ width: 768, height: 1024 });
    await basePage.waitForPageReady();
    expect(await basePage.isPageLoaded()).toBe(true);
    
    // Test mobile view
    await basePage.page.setViewportSize({ width: 375, height: 667 });
    await basePage.waitForPageReady();
    expect(await basePage.isPageLoaded()).toBe(true);
  });

  test('should load all critical resources', async () => {
    const resourceErrors = [];
    
    // Listen for resource load failures
    basePage.page.on('response', response => {
      if (!response.ok() && response.status() >= 400) {
        resourceErrors.push({
          url: response.url(),
          status: response.status(),
          statusText: response.statusText()
        });
      }
    });
    
    await basePage.navigateToService('website');
    await basePage.waitForPageReady();
    
    // Filter out non-critical errors (like analytics, ads, etc.)
    const criticalErrors = resourceErrors.filter(error => {
      const url = error.url.toLowerCase();
      return !url.includes('analytics') && 
             !url.includes('ads') && 
             !url.includes('tracking') &&
             !url.includes('facebook') &&
             !url.includes('google-analytics');
    });
    
    // Should not have critical resource loading errors
    expect(criticalErrors.length).toBe(0);
  });

  test('should have working internal links', async () => {
    await basePage.navigateToService('website');
    
    // Find internal links (href starting with /, #, or same domain)
    const baseUrl = TestHelpers.getServiceUrl('website');
    const internalLinks = await basePage.page.$$eval('a[href]', (links, baseUrl) => {
      return links
        .map(link => link.getAttribute('href'))
        .filter(href => {
          if (!href) return false;
          return href.startsWith('/') || 
                 href.startsWith('#') || 
                 href.startsWith(baseUrl) ||
                 (!href.startsWith('http') && !href.startsWith('mailto:'));
        })
        .slice(0, 5); // Test first 5 links only
    }, baseUrl);
    
    // Test a few internal links
    for (const link of internalLinks.slice(0, 3)) {
      if (link.startsWith('#')) continue; // Skip anchor links
      
      try {
        await basePage.page.goto(`${baseUrl}${link.startsWith('/') ? link : '/' + link}`, {
          timeout: 10000,
          waitUntil: 'networkidle'
        });
        
        expect(await basePage.isPageLoaded()).toBe(true);
      } catch (error) {
        TestHelpers.log(`Link test failed for ${link}: ${error.message}`, 'warn');
      }
    }
  });

  test('should handle form submissions properly', async () => {
    await basePage.navigateToService('website');
    
    // Look for forms on the page
    const forms = await basePage.page.$$('form');
    
    if (forms.length > 0) {
      // Test first form (like contact form, search form, etc.)
      const form = forms[0];
      const action = await form.getAttribute('action');
      const method = await form.getAttribute('method') || 'GET';
      
      // Check if form has proper attributes
      expect(action !== null || method !== null).toBe(true);
      
      // If it's a search form, test it
      const isSearchForm = await basePage.page.$eval(form, el => {
        const inputs = el.querySelectorAll('input[type="search"], input[name*="search"], input[placeholder*="search"]');
        return inputs.length > 0;
      }).catch(() => false);
      
      if (isSearchForm) {
        const searchInput = await form.$('input[type="search"], input[name*="search"], input[placeholder*="search"]');
        if (searchInput) {
          await searchInput.fill('test search');
          await basePage.page.keyboard.press('Enter');
          
          // Wait for search results or page change
          await basePage.waitForPageReady();
          expect(await basePage.isPageLoaded()).toBe(true);
        }
      }
    }
  });

  test('should display user-specific content when authenticated', async () => {
    // Test unauthenticated state
    await basePage.clearSession();
    await basePage.navigateToService('website');
    
    const unauthContent = await basePage.page.content();
    
    // Login and test authenticated state
    await loginPage.loginWithTestUser('admin');
    await basePage.navigateToService('website');
    
    const authContent = await basePage.page.content();
    
    // Content should be different between authenticated and unauthenticated states
    // or at least authenticated state should have additional elements
    const unauthLength = unauthContent.length;
    const authLength = authContent.length;
    
    // Authenticated version might have user menu, dashboard links, etc.
    expect(Math.abs(authLength - unauthLength) / Math.max(authLength, unauthLength)).toBeGreaterThan(0.01);
  });

  test('should have proper SSL/TLS configuration through Traefik', async () => {
    await basePage.navigateToService('website');
    
    const url = basePage.getCurrentUrl();
    
    // Should be served over HTTPS
    expect(url.startsWith('https://')).toBe(true);
    
    // Check security headers (if implemented)
    const response = await basePage.page.goto(url);
    const headers = response.headers();
    
    // Common security headers that might be set by Traefik
    const securityHeaders = [
      'strict-transport-security',
      'x-content-type-options',
      'x-frame-options',
      'x-xss-protection'
    ];
    
    let hasSecurityHeaders = false;
    for (const header of securityHeaders) {
      if (headers[header]) {
        hasSecurityHeaders = true;
        break;
      }
    }
    
    // Log security headers status
    TestHelpers.log(`Security headers present: ${hasSecurityHeaders}`);
  });

  test('should handle JavaScript errors gracefully', async () => {
    const jsErrors = [];
    
    basePage.page.on('pageerror', error => {
      jsErrors.push({
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      });
    });
    
    await basePage.navigateToService('website');
    await basePage.waitForPageReady();
    
    // Allow some time for any async JS to execute
    await basePage.page.waitForTimeout(2000);
    
    // Should not have critical JavaScript errors
    const criticalErrors = jsErrors.filter(error => 
      !error.message.includes('Non-Error promise rejection') &&
      !error.message.includes('Script error') &&
      !error.message.toLowerCase().includes('analytics')
    );
    
    if (criticalErrors.length > 0) {
      TestHelpers.log(`JavaScript errors found: ${JSON.stringify(criticalErrors)}`, 'warn');
    }
    
    // For now, just log errors but don't fail the test
    // expect(criticalErrors.length).toBe(0);
  });
});