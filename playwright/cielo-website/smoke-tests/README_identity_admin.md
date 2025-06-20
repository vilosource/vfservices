# Identity Admin Integration Test

## Overview

This test verifies that the Identity Admin interface works correctly with the real Identity Provider API, not just mock data.

## Test File

- `test_identity_admin.py` - Tests the complete Identity Admin workflow with real API calls

## What is Tested

### 1. User List View
- Verifies all 16 users are displayed (not filtered by empty URL parameters)
- Checks pagination info shows correct count
- Confirms specific users (alice, bob, charlie, david) are visible

### 2. User Detail View
- Tests clicking on a user to view their details
- Verifies user information is displayed correctly
- Confirms roles are shown properly

### 3. User Edit View
- Tests navigation to edit form
- Verifies form is populated with user data

### 4. Search and Filtering
- Tests searching for a specific user (alice)
- Verifies filtered results show only matching user
- Tests clearing filters to show all users again

## Prerequisites

- All services must be running (identity-provider, website, traefik)
- Alice user must exist with password "alicepassword" and identity_admin role
- Real API must be enabled (USE_MOCK_API = false in api-config.js)

## How to Run

### Using pytest (from container):
```bash
docker compose exec website-test python -m pytest playwright/cielo-website/smoke-tests/test_identity_admin.py -v
```

### Standalone (from host):
```bash
cd playwright/cielo-website/smoke-tests
python test_identity_admin.py
```

## Key Implementation Details

1. **Real API Integration**: The test uses the actual Identity Provider API endpoints, not mock data
2. **Empty Filter Fix**: The test verifies that empty URL parameters don't filter out all users
3. **JWT Authentication**: Uses cookie-based JWT authentication from the Identity Provider
4. **Pagination**: Confirms the API returns all users and pagination info is correct

## Troubleshooting

### Test fails with "Expected to see 16 users"
- Check if empty URL parameters are being sent (e.g., `?is_active=&has_role=`)
- Verify the frontend removes empty filter values before sending to API
- Check the backend doesn't interpret empty strings as filter values

### Authentication fails
- Ensure Alice's password is set to "alicepassword"
- Verify Alice has the identity_admin role
- Check JWT token is being properly set in cookies

### API returns no data
- Verify USE_MOCK_API is set to false in api-config.js
- Check Identity Provider service is running and accessible
- Ensure CORS is properly configured for cross-domain requests