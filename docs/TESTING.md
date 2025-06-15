# VF Services Testing Guide

## Overview

This document provides comprehensive guidance for Docker-based testing in the VF Services project. It covers development workflows, test execution strategies, maintenance procedures, and best practices for writing and running tests.

## Quick Start

### Development Commands
```bash
# Fast development tests (~11 seconds)
make test-dev

# Quick smoke tests (~30 seconds)  
make test-smoke

# Full enhanced test run (~10+ minutes)
make test-docker-enhanced

# Visual debugging with browser UI
make test-docker-headed

# Interactive debugging shell
make test-docker-debug
```

### Viewing Results
```bash
# View test status and recent runs
make test-status

# Start web interface for reports
make test-web

# Analyze specific test run
make test-analyze TEST_RUN_ID=<run_id>
```

## Testing Strategy

### Development Testing Pyramid

#### 1. **Smoke Tests** (~30 seconds)
- **Command:** `make test-smoke`
- **Purpose:** Instant feedback on basic functionality
- **When to use:** After every code change, before commits
- **Coverage:** Login, basic navigation, API health checks

#### 2. **Development Tests** (~2 minutes)  
- **Command:** `make test-dev`
- **Purpose:** Fast development feedback loop
- **When to use:** During active development, feature testing
- **Coverage:** Authentication flows, key user journeys, API integration (Chrome only)

#### 3. **Critical Path Tests** (~5 minutes)
- **Command:** `make test-critical`
- **Purpose:** Essential business logic verification
- **When to use:** Before pull requests, integration testing
- **Coverage:** End-to-end user flows, data persistence, security (Chrome only)

#### 4. **Component-Specific Tests** (~1-3 minutes each)
- **Authentication:** `make test-auth` - Login, logout, session management
- **API Tests:** `make test-api` - Backend integration, data validation
- **UI Tests:** `make test-ui` - Frontend components, user interactions
- **Chrome Only:** `make test-chrome` - Single browser comprehensive

#### 5. **Full E2E Tests** (~10+ minutes)
- **Command:** `make test-docker-enhanced`
- **Purpose:** Complete system validation
- **When to use:** Pre-release, CI/CD, comprehensive validation
- **Coverage:** All browsers, all scenarios, comprehensive reporting

## Running Specific Tests

### Individual Test Execution
```bash
# Run specific test file
make test-file FILE=auth/login.spec.js

# Run specific test within a file
make test-specific FILE=auth/login.spec.js TEST="should login successfully"

# Run all tests in a directory
make test-dir DIR=auth

# Run tests matching a pattern
make test-grep PATTERN="login"
make test-grep PATTERN="@smoke.*login"
make test-grep PATTERN="should.*successfully"

# List available tests and directories
make test-ls
```

### Common Patterns
```bash
# Test specific functionality you're working on
make test-file FILE=auth/login.spec.js       # Authentication
make test-file FILE=website/homepage.spec.js  # Frontend

# Test by component
make test-dir DIR=auth          # All auth tests
make test-dir DIR=website       # All website tests

# Search for specific test scenarios
make test-grep PATTERN="profile"           # All profile-related tests
make test-grep PATTERN="@critical"         # All critical tests
make test-grep PATTERN="should.*fail"      # All failure scenarios
```

## Development Workflow

### During Active Development
```bash
# Quick feedback after changes
make test-smoke

# Test specific file you're working on
make test-file FILE=auth/login.spec.js

# Test specific component you're working on
make test-auth    # If working on authentication
make test-api     # If working on backend
make test-ui      # If working on frontend
```

### Before Committing
```bash
# Run development test suite
make test-dev

# Or run critical path tests
make test-critical
```

### Before Pull Request
```bash
# Run comprehensive single-browser tests
make test-chrome

# Or run critical tests with analysis
make test-critical && make test-analyze TEST_RUN_ID=<latest>
```

### Pre-Release Testing
```bash
# Full comprehensive testing
make test-docker-enhanced
```

## Writing Tests

### Test Tagging Strategy

Use appropriate tags for proper test categorization:

#### Core Tags
- `@smoke` - Basic functionality, fastest tests
- `@fast` - Quick tests for development feedback
- `@critical` - Must-pass tests for releases
- `@dev` - Development-focused test subset

#### Component Tags  
- `@auth` - Authentication and authorization
- `@api` - Backend API testing
- `@ui` - Frontend user interface
- `@integration` - Cross-service integration

#### Browser Tags
- `@chrome` - Chrome-specific tests
- `@firefox` - Firefox-specific tests
- `@safari` - Safari/WebKit tests
- `@mobile` - Mobile browser tests

### Example Test Implementation
```javascript
// Critical authentication test
test('user login with valid credentials @auth @critical @smoke', async () => {
  // Test implementation
});

// Development-focused UI test
test('navigation menu displays correctly @ui @dev @fast', async () => {
  // Test implementation
});

// API integration test
test('user profile API returns correct data @api @integration', async () => {
  // Test implementation
});
```

### Best Practices for Test Writing
1. **Use descriptive test names** with appropriate tags
2. **Keep tests independent** - no dependencies between tests
3. **Clean up after tests** - reset state appropriately
4. **Use page objects** for reusable UI interactions
5. **Handle async operations** properly with awaits
6. **Add appropriate waits** - avoid hard delays, use smart waits

## Docker Infrastructure

### Container Architecture

The testing infrastructure uses multi-stage Docker containers:

#### **Playwright Runner Container**
- **Base:** `mcr.microsoft.com/playwright:v1.40.0-focal`
- **Purpose:** Execute tests with pre-installed browsers
- **Network:** Host networking for service connectivity
- **Volumes:** Live code mounting for development

#### **Test Analyzer Container**
- **Base:** `node:18-alpine`
- **Purpose:** Comprehensive result analysis and reporting
- **Features:** 9-category failure analysis, trend monitoring
- **Output:** HTML, JSON, and Markdown reports

#### **Service Setup Container**
- **Base:** `curlimages/curl:latest`
- **Purpose:** Health checks and service readiness validation
- **Dependencies:** Traefik, Website, Identity Provider services

### Key Configuration Files

- **`docker-compose.test.enhanced.yml`** - Enhanced test orchestration
- **`tests/playwright/docker/Dockerfile.playwright.enhanced`** - Multi-stage test container
- **`tests/playwright/docker/Dockerfile.analyzer`** - Analysis container
- **`tests/playwright.config.js`** - Playwright configuration
- **`tests/playwright/config/test-environments.json`** - Environment settings

## Result Analysis

### Automated Analysis System

The testing infrastructure includes comprehensive result analysis:

#### **9-Category Failure Analysis**
1. Browser/Infrastructure issues
2. Network/CORS problems  
3. Authentication failures
4. Service unavailability
5. Assertion errors
6. Timeout issues
7. Element not found
8. JavaScript errors
9. Other/uncategorized

#### **Advanced Features**
- **Pattern Detection:** Identifies flaky vs consistent failures
- **Performance Analysis:** Slowest/fastest tests, timing metrics
- **Trend Analysis:** Historical comparison framework
- **Critical Path Detection:** High-impact failure identification
- **Automated Recommendations:** Priority-based action suggestions

#### **Multi-Format Output**
- **HTML Reports:** Rich visual analysis with charts and metrics
- **JSON Data:** Machine-readable analysis for CI/CD integration
- **Markdown Summaries:** Quick overview for documentation

### Viewing Results

```bash
# Start web interface for reports
make test-web
# Visit http://localhost:8080

# Analyze latest run
make test-analyze TEST_RUN_ID=latest

# View recent test runs
make test-list

# Check system status
make test-status
```

## Maintenance

### Daily Operations

```bash
# Check test infrastructure health
make test-status

# Review latest test results
make test-web

# Run quick smoke tests
make test-smoke

# Clean Docker environment if needed
make test-docker-clean
```

### Weekly Maintenance

```bash
# Archive old results (>30 days)
make test-archive

# Check disk usage
du -sh test-results/ test-reports/

# Clean Docker resources
make test-docker-clean
docker system prune -f --volumes
```

### Performance Optimization

#### **Container Optimization**
- Multi-stage builds for faster startup
- Layer caching optimization
- Resource limits configuration
- Parallel execution tuning

#### **Test Execution Optimization**
- Single browser for development tests
- Selective tag-based filtering
- Optimized service wait times
- Minimal retries for faster feedback

## Troubleshooting

### Common Issues

#### **High Failure Rate (>20%)**
```bash
# Analyze recent failures
make test-analyze TEST_RUN_ID=latest

# Check service health
docker compose ps
docker compose logs traefik
```

#### **Slow Test Execution (>45 minutes)**
```bash
# Identify slow tests
make test-analyze TEST_RUN_ID=latest | grep -A 20 "Performance"

# Check container resources
docker stats --no-stream

# Increase parallel workers
make test-docker-enhanced TEST_PARALLEL=6
```

#### **Service Connection Issues**
```bash
# Interactive debugging
make test-docker-debug

# Check network connectivity from test container
curl -k https://vfservices.viloforge.com/api/status/
```

### Debug Mode

```bash
# Interactive debugging shell
make test-docker-debug

# Visual debugging with browser UI
make test-docker-headed

# Run specific tests with debugging
PWDEBUG=1 make test-file FILE=auth/login.spec.js
```

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run Docker Tests
  run: make test-ci-docker

- name: Upload Test Results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results-${{ github.run_id }}
    path: test-results/

- name: Upload Test Reports
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-reports-${{ github.run_id }}
    path: test-reports/
```

### Testing Strategy by Environment

#### **Feature Branches**
- Development tests (`make test-dev`)
- Component-specific tests as needed

#### **Pull Requests**  
- Critical path tests (`make test-critical`)
- Comprehensive analysis required

#### **Main Branch**
- Full E2E tests (`make test-docker-enhanced`)
- Complete result analysis and reporting

#### **Releases**
- Full comprehensive testing with all browsers
- Performance and security validation
- Historical comparison and trend analysis

## Success Metrics

### Key Performance Indicators
- **Test Reliability:** 95%+ success rate target
- **Analysis Accuracy:** Failure categorization precision >90%
- **Performance:** Average test execution <30 seconds for development tests
- **Coverage:** All critical user paths tested

### Monitoring
- Daily success rate trends
- Weekly performance analysis
- Monthly infrastructure reviews
- Quarterly strategy assessments

---

This comprehensive testing guide ensures efficient development workflows while maintaining high-quality standards for the VF Services project. Regular adherence to these practices will provide fast feedback loops during development and reliable quality assurance for releases.