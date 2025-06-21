# Identity Admin Dropdown Test

This test verifies that the Identity Admin link in the user dropdown menu works correctly in the cielo-website.

## Prerequisites

- User with `identity_admin` role exists in the system
- Default credentials: username `admin`, password `admin123!#QWERT`

## Running the Test

```bash
# From the project root
cd playwright/cielo-website/smoke-tests

# Run the test
pytest test_identity_admin_dropdown.py -v

# Run with custom credentials
IDENTITY_ADMIN_USER=myuser IDENTITY_ADMIN_PASSWORD=mypass pytest test_identity_admin_dropdown.py -v
```

## Test Coverage

1. **test_identity_admin_link_in_dropdown**: Verifies that:
   - The Identity Admin link appears in the dropdown for users with the `identity_admin` role
   - The link has the correct URL: `https://identity.vfservices.viloforge.com/admin/`
   - The admin icon is displayed

2. **test_identity_admin_link_navigation**: Verifies that:
   - Clicking the Identity Admin link navigates to the correct URL
   - The navigation works as expected

## Notes

- The test uses the traefik endpoint as per project guidelines
- The Identity Admin link only appears for users with the `identity_admin` role due to the `{% user_has_role 'identity_admin' %}` template tag