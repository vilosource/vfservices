# MaltaCentral Web Avatar Functionality Tests

This directory contains Playwright smoke tests for avatar functionality in the MaltaCentral Web application.

## Overview

These tests verify that user avatars are dynamically loaded from the Identity Provider and displayed correctly throughout the MaltaCentral Web interface.

## Test Coverage

### test_avatar_functionality.py
- **test_avatar_manager_loaded**: Verifies AvatarManager JavaScript is loaded and configured
- **test_avatar_elements_present**: Checks avatar elements exist in topbar and sidebar
- **test_avatar_displays_correctly**: Validates correct avatar image is displayed
- **test_sidebar_avatar_displays**: Ensures sidebar avatar matches topbar avatar
- **test_avatar_api_call**: Tests API communication with Identity Provider
- **test_avatar_caching**: Verifies avatar data is cached in sessionStorage
- **test_profile_page_avatar**: Checks avatars load on profile page
- **test_avatar_fallback_pattern**: Validates fallback avatar numbering logic

## Prerequisites

1. Docker environment running with all services
2. Identity Provider accessible at https://identity.vfservices.viloforge.com
3. MaltaCentral Web accessible at https://www.maltacentral.com
4. Admin user credentials: username `admin`, password `admin123`

## Running the Tests

### Run all avatar tests:
```bash
cd /home/jasonvi/GitHub/vfservices/playwright/maltacentral-web/smoke-tests
pytest test_avatar_functionality.py -v
```

### Run a specific test:
```bash
pytest test_avatar_functionality.py::TestAvatarFunctionality::test_avatar_displays_correctly -v
```

### Run with browser visible (non-headless):
```bash
pytest test_avatar_functionality.py --headed -v
```

### Run with slowmo for debugging:
```bash
pytest test_avatar_functionality.py --slowmo 1000 -v
```

## Expected Behavior

1. **Avatar Loading**: When a user logs in, JavaScript automatically fetches their profile from the Identity Provider
2. **Fallback Logic**: If no custom avatar exists, users get a numbered default avatar (1-12) based on their user ID
3. **Caching**: Avatar URLs are cached in sessionStorage for 5 minutes to improve performance
4. **Consistency**: The same avatar appears in all locations (topbar dropdown, sidebar user box)

## Common Issues

### Avatars not loading
- Check browser console for JavaScript errors
- Verify Identity Provider is accessible
- Ensure CORS is properly configured
- Check that `{{ block.super }}` is used in template inheritance

### Cross-Domain Limitations
- MaltaCentral is on `.maltacentral.com` domain while Identity Provider is on `.viloforge.com`
- JWT cookies cannot be shared across these different domains
- Avatar loading may be limited due to cross-origin restrictions
- The application may need to implement a backend proxy for avatar API calls

### Wrong avatar displayed
- Clear browser cache and sessionStorage
- Verify user ID in Identity Provider
- Check avatar fallback calculation
- Note: Due to cross-domain issues, avatars may default to avatar-1.jpg

### Test failures
- Ensure all services are running via `docker compose up`
- Verify SSL certificates are valid
- Check that test user credentials are correct

## Avatar Locations in UI

1. **Top Navigation Bar**: Dropdown menu trigger (right side)
2. **Left Sidebar**: User box at the top of sidebar
3. **Profile Page**: All avatar instances should update

## Technical Details

- Avatars are loaded via JavaScript from `/api/profile/` endpoint
- Default avatars are located in `/static/assets/images/users/avatar-[1-12].jpg`
- Custom avatars are stored in Identity Provider at `/media/avatars/`
- Avatar management script: `/static/js/avatar-management.js`

## Related Documentation

- [User Management Architecture](/dev-docs/user-management-architecture.md)
- [Django Template Best Practices](/dev-docs/DJANGO-TEMPLATE-BEST-PRACTICES.md)
- [JWT Authentication Guide](/dev-docs/JWT-AUTHENTICATION-GUIDE.md)