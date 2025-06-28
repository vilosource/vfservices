# Avatar Display Tests

This test suite verifies the avatar display functionality in the website Django application.

## Overview

The avatar functionality allows users to have custom profile pictures that are:
- Stored centrally in the Identity Provider
- Loaded dynamically via JavaScript API calls
- Displayed consistently across all VF Services applications

## Test Coverage

### `test_avatar_display_authenticated_user`
- Logs in as an authenticated user
- Verifies that the avatar image is loaded and visible
- Checks that the avatar source is either a custom URL or default avatar

### `test_avatar_display_guest_user`
- Tests the guest user experience
- Verifies that guest users see the default avatar
- Ensures no JavaScript errors occur for unauthenticated users

### `test_avatar_javascript_loading`
- Verifies that the AvatarManager JavaScript module is loaded
- Checks that the Identity Provider URL is configured correctly
- Ensures the JavaScript initialization works properly

## Running the Tests

1. Ensure all services are running:
   ```bash
   docker compose up -d
   ```

2. Run the avatar display tests:
   ```bash
   cd playwright/website/smoke-tests
   pytest test_avatar_display.py -v
   ```

3. To run a specific test:
   ```bash
   pytest test_avatar_display.py::test_avatar_display_authenticated_user -v
   ```

## Test Prerequisites

- Identity Provider service must be running at https://identity.vfservices.viloforge.com
- Website service must be running at https://website.vfservices.viloforge.com
- Test user credentials: admin / admin123 (Note: admin is a special case and doesn't follow the normal test password pattern)

## Implementation Details

The avatar system works as follows:

1. **Backend**: The Identity Provider stores avatar URLs as UserAttributes
2. **API**: The `/api/profile/` endpoint returns user data including avatar_url
3. **Frontend**: JavaScript fetches the profile data and updates avatar elements
4. **Fallback**: If no custom avatar exists, a numbered default avatar is used

## Troubleshooting

If tests fail:

1. Check that all services are running
2. Verify the test user exists and can log in manually
3. Check browser console for JavaScript errors
4. Ensure the avatar-management.js file is properly loaded
5. Verify CORS settings allow requests from website to Identity Provider

## Future Enhancements

- Test avatar upload functionality when UI is implemented
- Test avatar caching and refresh mechanisms
- Test avatar display across multiple browser sessions
- Performance tests for avatar loading with many concurrent users