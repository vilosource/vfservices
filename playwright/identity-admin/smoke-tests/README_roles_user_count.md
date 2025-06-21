# Identity Admin Roles User Count Tests

This test suite verifies that the user count is properly displayed on the Identity Admin roles page.

## Purpose

These tests were created to debug and prevent issues with the user count not being displayed on the roles page at https://vfservices.viloforge.com/admin/roles/

## Test Coverage

### 1. `test_roles_page_user_count_display`
- Verifies that each role displays a user count badge
- Takes screenshots for visual debugging
- Captures API responses for analysis
- Reports which roles are missing user counts

### 2. `test_roles_api_response_structure`
- Directly verifies the API response structure
- Ensures all roles have the `user_count` field
- Helps identify if the issue is API-side or frontend-side

### 3. `test_roles_page_performance`
- Checks page loading performance
- Captures JavaScript errors
- Verifies DataTable initialization
- Checks API client configuration

## Running the Tests

### Prerequisites
1. **Environment Access**: The tests require access to the VFServices environment. Ensure your machine can resolve:
   - `website.vfservices.viloforge.com`
   - `identity.vfservices.viloforge.com`
   
   Run the connectivity test first to verify:
   ```bash
   python playwright/identity-admin/smoke-tests/test_environment_connectivity.py
   ```

2. Ensure you have the test dependencies installed:
   ```bash
   pip install pytest playwright pytest-asyncio
   playwright install chromium
   ```

3. Test credentials are configured in the test file:
   - Username: `admin`
   - Password: `admin123!#QWERT`

### Run All Tests
```bash
cd /home/jasonvi/GitHub/vfservices
python -m pytest playwright/identity-admin/smoke-tests/test_roles_user_count.py -v -s
```

### Run Specific Test
```bash
# Test user count display
python -m pytest playwright/identity-admin/smoke-tests/test_roles_user_count.py::TestRolesUserCount::test_roles_page_user_count_display -v -s

# Test API response
python -m pytest playwright/identity-admin/smoke-tests/test_roles_user_count.py::TestRolesUserCount::test_roles_api_response_structure -v -s

# Test performance
python -m pytest playwright/identity-admin/smoke-tests/test_roles_user_count.py::TestRolesUserCount::test_roles_page_performance -v -s
```

### Run with Headed Browser (for visual debugging)
```bash
python -m pytest playwright/identity-admin/smoke-tests/test_roles_user_count.py -v -s --headed
```

## Debugging Output

The tests generate several debugging artifacts:

1. **Screenshots**:
   - `roles_page_loaded.png` - Full page after loading
   - `roles_table_content.png` - Close-up of the roles table
   - `error_screenshot.png` - Generated on test failure

2. **Console Output**:
   - API response details
   - Role-by-role analysis
   - JavaScript errors
   - Network errors

3. **Performance Trace**:
   - `trace.zip` - Can be viewed at https://trace.playwright.dev/

## Common Issues and Solutions

### Issue: User count shows as "N/A" or empty
**Debugging steps**:
1. Check API response in test output - does it include `user_count`?
2. Check for JavaScript errors in console output
3. Verify API client is using real API, not mock (`USE_MOCK_API = false`)

### Issue: API authentication fails
**Solution**: Ensure the test user exists and has admin privileges

### Issue: Page loads but table is empty
**Debugging steps**:
1. Check network errors in test output
2. Verify API endpoint is accessible
3. Check if mock API is being used instead of real API

## Expected Behavior

When tests pass, every role in the table should display:
- Service name (badge)
- Role name
- Display name
- Description
- **User count badge** (e.g., "5 users" or "1 user")

## Integration with CI/CD

These tests should be run:
- On every PR that modifies identity admin code
- As part of the nightly test suite
- After deployments to verify functionality

## Maintenance

If the UI structure changes, update:
- CSS selectors in the test
- Column numbers for user count (currently 5th column)
- Screenshot names if needed