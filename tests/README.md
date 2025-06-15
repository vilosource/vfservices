# VF Services E2E Testing with Playwright

This directory contains end-to-end tests for the VF Services application using Playwright. The tests are designed to work with the Traefik reverse proxy setup and test all services through their production-like routing.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- All VF Services running via docker-compose

### Running Tests Locally

1. **Start the services:**
   ```bash
   # From the project root
   docker-compose up -d
   ```

2. **Install test dependencies:**
   ```bash
   cd tests
   npm install
   npx playwright install
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Run tests:**
   ```bash
   # Run all tests
   npm test
   
   # Run specific browser
   npx playwright test --project=chromium
   
   # Run with UI mode
   npm run test:ui
   
   # Run in headed mode (see browser)
   npm run test:headed
   ```

### Running Tests with Docker

```bash
# From project root
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --build playwright
```

## Test Structure

```
tests/
├── playwright/
│   ├── config/           # Test configuration
│   ├── pages/           # Page Object Models
│   ├── tests/           # Test suites
│   │   ├── auth/        # Authentication tests
│   │   ├── website/     # Website-specific tests
│   │   ├── billing/     # Billing service tests
│   │   ├── inventory/   # Inventory service tests
│   │   └── infrastructure/ # Traefik and infrastructure tests
│   └── utils/           # Test utilities and helpers
└── package.json         # Dependencies and scripts
```

## Test Categories

### Authentication Tests (`tests/auth/`)
- **Login/Logout**: Basic authentication flows
- **SSO**: Single Sign-On across services
- **Session Management**: Token handling and expiration
- **Cross-domain Authentication**: Service-to-service auth

### Website Tests (`tests/website/`)
- **Homepage**: Basic functionality and loading
- **Navigation**: Internal links and routing
- **Responsive Design**: Mobile and desktop layouts
- **User Experience**: Forms, interactions, performance

### Infrastructure Tests (`tests/infrastructure/`)
- **Traefik Routing**: Service routing and load balancing
- **SSL/TLS**: Certificate handling and HTTPS redirection
- **Error Handling**: 404s, timeouts, and error pages
- **Health Checks**: Service availability monitoring

### Service-Specific Tests
- **Billing Service**: API endpoints and UI integration
- **Inventory Service**: Data management and workflows

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Base URLs
BASE_URL=https://vfservices.viloforge.com
IDENTITY_URL=https://identity.vfservices.viloforge.com
WEBSITE_URL=https://website.vfservices.viloforge.com
BILLING_URL=https://billing.vfservices.viloforge.com
INVENTORY_URL=https://inventory.vfservices.viloforge.com

# Test Environment
TEST_ENV=development

# Test Credentials
TEST_ADMIN_USERNAME=admin
TEST_ADMIN_PASSWORD=admin123
```

### Test Environment Configuration

Test environments are defined in `playwright/config/test-environments.json`:

- **Development**: Local Docker setup
- **Staging**: Staging environment
- **Production**: Read-only production tests

## Page Object Model

Tests use the Page Object Model pattern for maintainability:

### BasePage
Common functionality for all pages:
- Navigation between services
- Traefik route handling
- Authentication state checking
- Screenshot and error capture

### LoginPage
Authentication-specific functionality:
- Login/logout operations
- SSO verification
- Cross-domain authentication testing

### Service-Specific Pages
Each service has its own page objects with specific selectors and methods.

## Utilities

### TestHelpers
- Environment configuration loading
- Test data generation
- Logging and screenshot utilities
- Retry logic with exponential backoff

### ApiClient
- REST API testing capabilities
- Authentication token management
- Test data setup and cleanup
- Health check verification

## CI/CD Integration

### GitHub Actions

The test suite integrates with GitHub Actions (`.github/workflows/e2e-tests.yml`):

- **Triggers**: Push to main/develop, PRs, scheduled runs
- **Matrix Strategy**: Tests across Chromium, Firefox, WebKit
- **Artifacts**: Test reports, screenshots, service logs
- **Parallel Execution**: Multiple browsers simultaneously

### Local CI Simulation

```bash
# Simulate CI environment
export CI=true
npm test
```

## Debugging Tests

### Interactive Debugging

```bash
# Debug mode (opens browser DevTools)
npm run test:debug

# UI mode (interactive test runner)
npm run test:ui

# Headed mode (visible browser)
npm run test:headed
```

### Screenshots and Videos

- Screenshots are taken on test failures
- Videos are recorded for failed tests
- Trace files capture detailed execution information

### Service Logs

When tests fail, collect service logs:

```bash
# View specific service logs
docker-compose logs traefik
docker-compose logs identity-provider
docker-compose logs website
```

## Writing New Tests

### Basic Test Structure

```javascript
const { test, expect } = require('@playwright/test');
const LoginPage = require('../../pages/login-page');
const TestHelpers = require('../../utils/helpers');

test.describe('My Test Suite', () => {
  let loginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.clearAuth();
  });

  test('should do something', async () => {
    await loginPage.loginWithTestUser('admin');
    
    // Your test logic here
    expect(await loginPage.isLoginSuccessful()).toBe(true);
  });
});
```

### Best Practices

1. **Clean State**: Always start tests with clean authentication state
2. **Wait Strategies**: Use proper waits for Traefik routing and dynamic content
3. **Error Handling**: Implement retry logic for flaky network operations
4. **Test Data**: Use generated test data to avoid conflicts
5. **Cleanup**: Clean up test data in teardown hooks
6. **Assertions**: Use meaningful assertions with proper error messages

### Adding New Page Objects

1. Extend `BasePage` for common functionality
2. Define service-specific selectors
3. Implement reusable methods for common operations
4. Add proper error handling and logging

### Adding New Test Suites

1. Create appropriate directory structure under `tests/`
2. Follow existing naming conventions (`*.spec.js`)
3. Use descriptive test names and organize with `test.describe()`
4. Add proper setup and teardown hooks

## Troubleshooting

### Common Issues

1. **Service Not Ready**: Increase wait times in global setup
2. **SSL Certificate Errors**: Ensure `ignoreHTTPSErrors: true` in config
3. **Authentication Failures**: Check test user credentials in environment config
4. **Flaky Tests**: Add retry logic and proper wait strategies
5. **Docker Issues**: Ensure all services are healthy before running tests

### Debug Commands

```bash
# Check service health
docker-compose ps
docker-compose logs traefik

# Test service accessibility
curl -k https://vfservices.viloforge.com
curl -k https://identity.vfservices.viloforge.com

# Run single test with debug output
npx playwright test tests/auth/login.spec.js --debug

# Generate test report
npx playwright show-report
```

## Performance Considerations

- Tests run in parallel by default
- Use `test.describe.configure({ mode: 'serial' })` for dependent tests
- Minimize test data setup/teardown
- Use API calls for data operations when possible
- Implement proper cleanup to avoid resource leaks

## Security Considerations

- Never commit real credentials to the repository
- Use environment variables for sensitive configuration
- Implement proper test user management
- Rotate test credentials regularly
- Monitor test user activity in production environments

## Contributing

1. Follow existing patterns and conventions
2. Add tests for new features and bug fixes
3. Ensure tests pass locally before submitting PRs
4. Update documentation for new test categories
5. Consider test maintainability and readability