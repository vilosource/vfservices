# Playwright Testing Specification for VF Services

## Overview

This document outlines the implementation plan for end-to-end testing using Playwright to test the VF Services website through Traefik reverse proxy configuration.

## Current Architecture

### Service Stack
- **Traefik v3.4**: Reverse proxy with SSL termination
- **Django Services**: Multiple containerized Django applications
  - Identity Provider (identity.domain.com)
  - Website (website.domain.com / domain.com)
  - Billing API (billing.domain.com)
  - Inventory API (inventory.domain.com)
- **PostgreSQL**: Database backend
- **Docker Compose**: Container orchestration

### Current Testing Setup
- Django's built-in test framework for unit/integration tests
- Custom test files found in each service module
- No current end-to-end testing infrastructure

## Playwright Implementation Plan

### 1. Project Structure

```
/tests/
├── playwright/
│   ├── config/
│   │   ├── playwright.config.js
│   │   └── test-environments.json
│   ├── fixtures/
│   │   ├── test-data.json
│   │   └── users.json
│   ├── pages/
│   │   ├── base-page.js
│   │   ├── login-page.js
│   │   ├── dashboard-page.js
│   │   └── service-pages/
│   ├── tests/
│   │   ├── auth/
│   │   ├── website/
│   │   ├── billing/
│   │   └── inventory/
│   ├── utils/
│   │   ├── helpers.js
│   │   └── api-client.js
│   └── docker/
│       └── Dockerfile.playwright
├── package.json
└── docker-compose.test.yml
```

### 2. Testing Environment Configuration

#### Docker Compose Test Environment
Create `docker-compose.test.yml` that extends the main compose file:

```yaml
services:
  playwright:
    build:
      context: ./tests/playwright/docker
      dockerfile: Dockerfile.playwright
    volumes:
      - ./tests:/tests
      - ./test-results:/test-results
    networks:
      - vfnet
    environment:
      - BASE_URL=https://vfservices.viloforge.com
      - IDENTITY_URL=https://identity.vfservices.viloforge.com
      - WEBSITE_URL=https://website.vfservices.viloforge.com
      - BILLING_URL=https://billing.vfservices.viloforge.com
      - INVENTORY_URL=https://inventory.vfservices.viloforge.com
    depends_on:
      - traefik
      - website
      - identity-provider
      - billing-api
      - inventory-api
```

#### Playwright Configuration
Configure `playwright.config.js` to work with Traefik:

```javascript
module.exports = {
  testDir: './tests',
  timeout: 30000,
  expect: {
    timeout: 5000
  },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: process.env.BASE_URL || 'https://vfservices.viloforge.com',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    ignoreHTTPSErrors: true, // For self-signed certificates in dev
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'docker-compose up -d',
    port: 443,
    reuseExistingServer: !process.env.CI,
  },
};
```

### 3. Test Categories

#### Authentication Tests
- **SSO Login Flow**: Test cross-service authentication via Identity Provider
- **Logout Functionality**: Verify logout across all services
- **Session Management**: Test JWT token handling and expiration
- **Unauthorized Access**: Verify redirects for protected routes

#### Website Tests
- **Homepage Navigation**: Test main website functionality
- **User Dashboard**: Verify authenticated user experience
- **Cross-service Links**: Test navigation between services

#### API Service Tests
- **Billing API**: Test billing interface through web UI
- **Inventory API**: Test inventory management interface
- **Service Integration**: Verify data flow between services

#### Infrastructure Tests
- **SSL/TLS**: Verify certificate handling through Traefik
- **Load Balancing**: Test service availability and routing
- **Error Handling**: Test 404/500 error pages through Traefik

### 4. Page Object Model

#### Base Page Class
```javascript
class BasePage {
  constructor(page) {
    this.page = page;
    this.baseURL = process.env.BASE_URL;
  }
  
  async navigateToService(service) {
    const serviceUrls = {
      'website': process.env.WEBSITE_URL,
      'identity': process.env.IDENTITY_URL,
      'billing': process.env.BILLING_URL,
      'inventory': process.env.INVENTORY_URL
    };
    await this.page.goto(serviceUrls[service]);
  }
  
  async waitForTraefikRoute() {
    // Wait for Traefik routing to complete
    await this.page.waitForLoadState('networkidle');
  }
}
```

#### Authentication Flow
```javascript
class LoginPage extends BasePage {
  async login(username, password) {
    await this.navigateToService('identity');
    await this.page.fill('#username', username);
    await this.page.fill('#password', password);
    await this.page.click('button[type="submit"]');
    await this.waitForTraefikRoute();
  }
  
  async verifySSO() {
    // Verify SSO cookie is set across domains
    const cookies = await this.page.context().cookies();
    const ssoCookie = cookies.find(c => c.name.includes('sso'));
    expect(ssoCookie).toBeDefined();
  }
}
```

### 5. Test Data Management

#### Environment-specific Test Data
```json
{
  "environments": {
    "development": {
      "baseUrl": "https://vfservices.viloforge.com",
      "testUsers": {
        "admin": {
          "username": "admin",
          "password": "admin123"
        },
        "user": {
          "username": "testuser",
          "password": "testpass"
        }
      }
    },
    "staging": {
      "baseUrl": "https://staging.vfservices.viloforge.com",
      "testUsers": {
        "admin": {
          "username": "staging_admin",
          "password": "staging_pass"
        }
      }
    }
  }
}
```

### 6. Traefik-Specific Considerations

#### DNS Resolution
- Configure test runner to resolve service domains to localhost
- Use Docker network internal DNS for service-to-service communication
- Handle SSL certificate validation for development environments

#### Route Testing
- Test all Traefik routing rules defined in docker-compose labels
- Verify subdomain routing (identity.domain.com, billing.domain.com)
- Test root domain routing to website service
- Validate HTTPS redirection from HTTP

#### Load Balancer Testing
- Test service availability through Traefik
- Verify proper header forwarding (`passHostHeader=true`)
- Test service health checks and failover

### 7. CI/CD Integration

#### GitHub Actions Workflow
```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Start services
        run: docker-compose -f docker-compose.yml -f docker-compose.test.yml up -d
      - name: Wait for services
        run: ./scripts/wait-for-services.sh
      - name: Run Playwright tests
        run: docker-compose exec playwright npm run test
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: test-results/
```

### 8. Monitoring and Reporting

#### Test Reports
- HTML reports with screenshots and videos
- Test execution metrics and timing
- Cross-browser compatibility reports
- Service availability and response time metrics

#### Error Handling
- Capture network logs for failed requests
- Screenshot on test failure
- Video recording for complex user flows
- Traefik access logs correlation with test failures

### 9. Implementation Timeline

1. **Phase 1**: Setup basic Playwright infrastructure and Docker configuration
2. **Phase 2**: Implement authentication and basic navigation tests
3. **Phase 3**: Add service-specific test suites
4. **Phase 4**: Implement CI/CD integration and reporting
5. **Phase 5**: Add performance and load testing capabilities

### 10. Maintenance and Best Practices

#### Test Organization
- Group tests by service and functionality
- Use descriptive test names and documentation
- Implement proper cleanup after test runs
- Regular test data refresh and maintenance

#### Performance Considerations
- Run tests in parallel where possible
- Use test fixtures to minimize setup time
- Implement proper waiting strategies for dynamic content
- Monitor test execution time and optimize slow tests

## Dependencies

```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "dotenv": "^16.0.0"
  }
}
```

## Getting Started

1. Install Playwright and dependencies
2. Configure test environment variables
3. Build and start test environment with Docker Compose
4. Run initial test suite to verify setup
5. Implement additional test cases based on application requirements

This specification provides a comprehensive framework for implementing Playwright testing that works seamlessly with the existing Traefik and Docker Compose infrastructure.