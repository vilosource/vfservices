# Azure Costs API Playwright Smoke Tests

This directory contains Playwright-based smoke tests for the Azure Costs API service. The tests verify that the API endpoints are accessible through Traefik and functioning correctly.

## Test Coverage

### API Endpoints Tested

1. **Health Check Endpoint** (`/api/health`)
   - Verifies the service is running and healthy
   - Tests public access (no authentication required)
   - Validates response format and content

2. **Private Endpoint** (`/api/private`)
   - Tests authentication requirement
   - Verifies JWT token validation
   - Validates user information in response

3. **RBAC Test Endpoint** (`/api/test-rbac`)
   - Tests RBAC/ABAC integration
   - Verifies role and attribute handling
   - Validates access control
   - Returns user information with roles and attributes in a nested structure

### Test Files

- **`test_azure_costs_api.py`**: Direct API tests using Playwright's request context
  - Health endpoint validation
  - Authentication tests
  - RBAC functionality tests
  - CORS header validation
  - Error handling tests

- **`test_azure_costs_browser.py`**: Browser-based tests simulating user interactions
  - Browser navigation to API endpoints
  - Integration with CIELO website
  - Performance testing
  - HTTP method validation

- **`test_azure_costs_policies.py`**: ABAC (Attribute-Based Access Control) policy tests
  - Role-based access control (costs_admin, costs_manager, costs_viewer)
  - Subscription-based access control
  - Cost center access control
  - Budget limit enforcement
  - Export permissions validation
  - Policy enforcement for different user personas

## Prerequisites

1. **Python 3.8+** installed
2. **Playwright** browsers installed
3. **Azure Costs API** service running and accessible via Traefik
4. **Identity Provider** service running for authentication
5. **Test user account** created in the identity provider

## Installation

1. Navigate to the test directory:
   ```bash
   cd playwright/azure-costs/smoke-tests
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

## Test Users and ABAC Policies

### Demo Users
The policy tests use the following demo users with specific roles and attributes:

| Username | Password | Role | Subscriptions | Cost Centers | Budget Limit | Can Export |
|----------|----------|------|---------------|--------------|--------------|------------|
| admin | admin123 | costs_admin | sub-001, sub-002, sub-003 | cc-001, cc-002 | $1,000,000 | Yes |
| alice | alice123 | costs_manager | sub-001, sub-002 | cc-001 | $50,000 | Yes |
| bob | bob123 | costs_viewer | sub-001 | None | $0 | No |

### ABAC Policies Implemented

The Azure Costs service implements the following ABAC policies in `/azure-costs/azure_costs/policies.py`:

1. **Cost Viewing** (`costs_view`): Controls who can view Azure costs
2. **Budget Management** (`budget_create`, `budget_edit`, `budget_delete`): Controls budget operations
3. **Report Export** (`report_export`): Controls who can export cost reports
4. **Subscription Access** (`subscription_view`, `subscription_manage`): Controls subscription visibility
5. **Cost Center Access** (`cost_center_view`, `cost_center_manage`): Controls cost center operations
6. **Alert Management** (`alert_view`, `alert_manage`): Controls cost alert operations
7. **Budget Approval** (`budget_approve`, `budget_approval_required`): Controls budget approval workflow

## Configuration

The tests can be configured using environment variables:

### Required Configuration

- `AZURE_COSTS_BASE_URL`: Base URL for Azure Costs API (default: `https://azure-costs.cielo.viloforge.com`)
- `IDENTITY_PROVIDER_URL`: Identity provider URL (default: `https://identity.cielo.viloforge.com`)
- `TEST_USERNAME`: Username for test authentication (default: `testuser`)
- `TEST_PASSWORD`: Password for test authentication (default: `testpass123`)

### Optional Configuration

- `HEADLESS`: Run browser in headless mode (default: `true`)
- `SLOW_MO`: Slow down operations by specified milliseconds (default: `0`)
- `DEFAULT_TIMEOUT`: Default timeout in milliseconds (default: `30000`)
- `SCREENSHOT_ON_FAILURE`: Take screenshots on test failure (default: `true`)
- `RECORD_VIDEO`: Record videos of test execution (default: `false`)
- `IGNORE_HTTPS_ERRORS`: Ignore HTTPS certificate errors (default: `true`)

### Setting Environment Variables

Create a `.env` file in the test directory:

```bash
AZURE_COSTS_BASE_URL=https://azure-costs.cielo.viloforge.com
IDENTITY_PROVIDER_URL=https://identity.cielo.viloforge.com
TEST_USERNAME=testuser
TEST_PASSWORD=testpass123
HEADLESS=true
```

Or export them in your shell:

```bash
export AZURE_COSTS_BASE_URL=https://azure-costs.cielo.viloforge.com
export TEST_USERNAME=testuser
export TEST_PASSWORD=testpass123
```

## Running the Tests

### Run all tests:
```bash
pytest -v
```

### Run specific test file:
```bash
pytest test_azure_costs_api.py -v
```

### Run specific test:
```bash
pytest test_azure_costs_api.py::TestAzureCostsAPI::test_health_endpoint -v
```

### Run policy tests:
```bash
# Run all policy tests
pytest test_azure_costs_policies.py -v

# Run specific policy test
pytest test_azure_costs_policies.py::TestAzureCostsPolicies::test_costs_admin_full_access -v

# Run tests for a specific role
pytest test_azure_costs_policies.py -k "admin" -v
pytest test_azure_costs_policies.py -k "manager" -v
pytest test_azure_costs_policies.py -k "viewer" -v
```

### Run tests with markers:
```bash
# Run only API tests
pytest -m api -v

# Run only browser tests
pytest -m browser -v

# Run only tests requiring authentication
pytest -m auth -v

# Run all except slow tests
pytest -m "not slow" -v
```

### Run tests in headed mode (see browser):
```bash
HEADLESS=false pytest -v
```

### Run tests with video recording:
```bash
RECORD_VIDEO=true pytest -v
```

### Run tests with detailed output:
```bash
pytest -v -s --tb=short
```

## Test Results

- **Passed tests**: Show with green checkmarks (✓)
- **Failed tests**: Show with red X marks and error details
- **Skipped tests**: Show with yellow warnings (e.g., when authentication fails)

### Screenshots

If `SCREENSHOT_ON_FAILURE=true`, screenshots of failed tests are saved to the `./screenshots` directory.

### Videos

If `RECORD_VIDEO=true`, video recordings are saved to the `./videos` directory.

## Debugging Failed Tests

1. **Run in headed mode** to see what's happening:
   ```bash
   HEADLESS=false pytest test_azure_costs_api.py::TestAzureCostsAPI::test_private_endpoint_with_auth -v
   ```

2. **Add slow motion** to see actions clearly:
   ```bash
   HEADLESS=false SLOW_MO=1000 pytest -v
   ```

3. **Check screenshots** in the `./screenshots` directory

4. **Enable debug logging**:
   ```bash
   pytest -v -s --log-cli-level=DEBUG
   ```

## Common Issues and Solutions

### Issue: SSL Certificate Errors
**Solution**: Set `IGNORE_HTTPS_ERRORS=true` or use valid certificates

### Issue: Authentication Fails
**Solution**: 
- Verify test user exists in identity provider
- Check credentials are correct
- Ensure identity provider is accessible

### Issue: Timeouts
**Solution**: Increase timeout values:
```bash
DEFAULT_TIMEOUT=60000 pytest -v
```

### Issue: Cannot Connect to Service
**Solution**:
- Verify services are running: `docker compose ps`
- Check Traefik routing: `docker compose logs traefik`
- Verify domains are accessible

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Azure Costs API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd playwright/azure-costs/smoke-tests
          pip install -r requirements.txt
          playwright install chromium
      
      - name: Run tests
        env:
          AZURE_COSTS_BASE_URL: ${{ secrets.AZURE_COSTS_BASE_URL }}
          TEST_USERNAME: ${{ secrets.TEST_USERNAME }}
          TEST_PASSWORD: ${{ secrets.TEST_PASSWORD }}
        run: |
          cd playwright/azure-costs/smoke-tests
          pytest -v --junit-xml=test-results.xml
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: playwright/azure-costs/smoke-tests/test-results.xml
```

## Extending the Tests

To add new tests:

1. Create a new test method in the appropriate test class
2. Use appropriate markers (`@pytest.mark.api`, `@pytest.mark.auth`, etc.)
3. Follow the existing naming convention: `test_<feature>_<scenario>`
4. Add documentation for what the test verifies
5. Update this README if adding new configuration options

Example:
```python
@pytest.mark.api
@pytest.mark.auth
def test_cost_data_endpoint(self, page: Page):
    """Test the cost data endpoint returns Azure cost information."""
    token = self.get_jwt_token()
    response = page.request.get(
        f"{BASE_URL}/api/costs",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status == 200
    data = response.json()
    assert "costs" in data
    assert isinstance(data["costs"], list)
```

## Maintenance

- Update Playwright version regularly: `pip install --upgrade playwright pytest-playwright`
- Review and update test coverage when new endpoints are added
- Monitor test execution times and mark slow tests appropriately
- Clean up old screenshots and videos periodically