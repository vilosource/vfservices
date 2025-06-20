# CIELO Website Integration Tests

This directory contains integration tests that verify cross-service authentication and authorization between CIELO and other services.

## Tests

### test_azure_costs_access.py

This test verifies that users authenticated through CIELO can access Azure Costs API endpoints.

**Test Scenarios:**
1. **test_alice_azure_costs_api_access**: 
   - Logs in as user 'alice' through CIELO website
   - Verifies successful authentication with JWT token
   - Attempts to access Azure Costs API private endpoint (`https://azure-costs.cielo.viloforge.com/api/private`)
   - Verifies alice is authorized (expects 200 OK response)
   - Takes screenshots at each step for debugging

2. **test_alice_azure_costs_api_data_access**:
   - Quick login as alice
   - Tests multiple Azure Costs API endpoints:
     - `/api/private` - Private API root
     - `/api/private/costs` - Costs data
     - `/api/private/subscriptions` - Subscriptions
     - `/api/private/budgets` - Budgets
   - Reports which endpoints are accessible

## Running the Tests

### Prerequisites
1. Ensure all services are running via docker compose:
   ```bash
   docker compose up -d
   ```

2. Install Playwright and dependencies:
   ```bash
   cd playwright/cielo-website/integration-tests
   pip install playwright pytest
   playwright install chromium
   ```

### Running Individual Tests

Run the Azure Costs access test:
```bash
python test_azure_costs_access.py
```

Or using pytest:
```bash
pytest test_azure_costs_access.py -v
```

### Running All Integration Tests

```bash
pytest . -v
```

### Running with Visible Browser (for debugging)

Modify the test to use `headless=False`:
```python
browser = p.chromium.launch(headless=False)
```

## Expected Results

- User alice should be able to:
  1. Successfully log in to CIELO
  2. Receive authentication tokens (JWT)
  3. Access Azure Costs API private endpoints without additional authentication
  4. Receive 200 OK responses from the API

## Screenshots

The tests generate the following screenshots:
- `alice_cielo_login.png` - Login form filled with alice's credentials
- `alice_cielo_logged_in.png` - CIELO after successful login
- `alice_azure_costs_api_response.png` - Azure Costs API response
- `alice_test_error.png` - Error state (if test fails)

## Troubleshooting

1. **401 Unauthorized**: Check if the authentication token is properly shared between services
2. **403 Forbidden**: Verify alice has the correct roles in the identity provider
3. **Connection errors**: Ensure all services are running and accessible via Traefik
4. **SSL errors**: The test uses `ignore_https_errors=True` for local development

## Notes

- Tests use Traefik endpoints as specified in CLAUDE.md
- The test assumes alice has proper RBAC roles to access both CIELO and Azure Costs
- JWT tokens should be properly shared across the `.viloforge.com` domain