# Identity Admin Playwright Tests

This directory contains Playwright tests for the Identity Admin application.

## Overview

The Identity Admin app provides a web interface for managing users, roles, and services in the VFServices Identity Provider.

## Current Status

### Completed
- ✅ Identity Admin Django app created in `common/apps/identity_admin`
- ✅ App integrated into website project
- ✅ URL routing configured at `/admin/`
- ✅ Base templates and views created
- ✅ Authentication decorator with RBAC checks
- ✅ API client for Identity Provider integration
- ✅ Service registration scripts for RBAC setup

### Known Issues
- ⚠️ JWT tokens from web login don't include user_id field
- ⚠️ JWTUser objects in website have None for id/pk attributes
- ⚠️ Permission checks require user_id to fetch RBAC attributes

### Workarounds
To make the identity admin work, we need to fix the JWT token issue. Options:
1. Update Identity Provider to include user_id in web login JWT tokens
2. Modify the decorator to lookup user by username instead of ID
3. Create local User records in website database

## Test Scripts

### Setup Scripts
- `register_website_service.py` - Registers the website service with Identity Provider
- `register_identity_service.py` - Registers the identity_provider service with itself
- `setup_admin_role.py` - Grants identity_admin role to the admin user

### Test Files
- `test_identity_admin_basic.py` - Tests login and dashboard access
- `test_identity_admin_simple.py` - Simple connectivity test

## Running Tests

1. First run the setup scripts:
```bash
python register_identity_service.py
python register_website_service.py  
python setup_admin_role.py
```

2. Run the tests:
```bash
pytest test_identity_admin_basic.py -v
```

## Next Steps

1. Fix JWT token to include user_id
2. Complete dashboard implementation
3. Implement user list view with DataTables
4. Add user create/edit functionality
5. Implement role assignment interface
6. Add comprehensive test coverage