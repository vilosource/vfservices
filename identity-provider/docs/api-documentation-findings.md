# Identity Provider API Documentation Findings

This document outlines the discrepancies found between the documented API (api.md) and the actual implementation in the identity-provider codebase.

## Summary of Findings

After analyzing the identity-provider codebase and comparing it with the api.md documentation, several significant discrepancies were found between what is documented and what is actually implemented.

## Major Discrepancies

### 1. Logout API Endpoint

**Documentation States:**
- Endpoint: `POST /api/logout/`
- Headers: Requires authentication
- Response: 200 OK with empty body

**Actual Implementation:**
- **NO API logout endpoint exists**
- Only web-based logout at `/logout/` (GET request)
- The web logout clears JWT cookies and redirects
- API endpoints list in `APIInfoView` does not include `/api/logout/`

**Impact:** Applications expecting to use `/api/logout/` will receive a 404 error.

### 2. Login API Response Format

**Documentation States:**
```json
{
    "token": "jwt_token_string",
    "user": {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "first_name": "Admin",
        "last_name": "User"
    }
}
```

**Actual Implementation:**
```json
{
    "token": "jwt_token_string"
}
```

**Impact:** The actual response only includes the token, not user information.

### 3. Service Registration Endpoint

**Documentation States:**
- Endpoint: `POST /api/register-manifest/`

**Actual Implementation:**
- Endpoint: `POST /api/services/register/`

**Impact:** Wrong endpoint URL in documentation.

### 4. Admin API URL Structure

**Documentation States:**
- User endpoints like `/api/admin/users/{id}/set-password/`

**Actual Implementation:**
- Using ViewSets with different URL patterns
- Set password: `/api/admin/users/{id}/set_password/` (underscore not hyphen)
- Uses DRF ViewSet action patterns

### 5. Delete User Behavior

**Documentation States:**
- Endpoint: `DELETE /api/admin/users/{id}/`
- Response includes: `{"status": "User deactivated successfully"}`

**Actual Implementation:**
- Returns 204 No Content (no response body)
- Performs soft delete (sets `is_active=False`)

### 6. Audit Log Implementation

**Documentation States:**
- Full audit log API with filtering and detailed responses

**Actual Implementation:**
- Currently returns empty results (placeholder implementation)
- The `AuditLogView.get()` method always returns:
```python
{
    'results': [],
    'count': 0
}
```

### 7. Authentication Classes

**Documentation States:**
- Uses standard JWT Bearer token authentication

**Actual Implementation:**
- Admin API uses custom `JWTCookieAuthentication` class
- Designed to work with JWT cookies without triggering CSRF checks
- Different from standard Bearer token authentication

### 8. Bulk Operations Response

**Documentation Shows Different Field Names:**
- Uses "assignments" in request

**Actual Implementation Differences:**
- Response includes "success" count field not documented
- Returns 201 if any succeed, 400 only if all fail

## Minor Discrepancies

### 1. Pagination Parameters

- Documentation mentions generic pagination
- Implementation uses specific `StandardPagination` class with:
  - Default page_size: 50
  - Max page_size: 100
  - Query param: `page_size`

### 2. User Roles Endpoint Format

- Documentation shows roles nested in user detail
- Implementation has separate `/api/admin/users/{id}/roles/` endpoint
- Role revocation uses nested URL: `/api/admin/users/{id}/roles/{role_id}/`

### 3. Error Response Formats

- Documentation shows generic error formats
- Implementation uses DRF standard error responses
- Some custom error messages differ from documented ones

## Missing Documentation

### 1. Available Endpoints Not Documented

- `/api/` - API information endpoint
- `/api/status/` - Health check endpoint
- `/api/refresh-user-cache/` - Cache refresh endpoint
- Various admin ViewSet actions

### 2. Query Parameters Not Fully Documented

- User list supports additional filters not documented
- Ordering parameters not fully specified

### 3. Permission Requirements

- All admin endpoints require `identity_admin` role
- This is enforced by `IsIdentityAdmin` permission class
- Not clearly stated for each endpoint

## Recommendations

1. **Update Logout Documentation:** Remove the `/api/logout/` endpoint from documentation or implement it
2. **Fix Login Response:** Update documentation to match actual response format
3. **Correct Endpoint URLs:** Fix service registration and other incorrect URLs
4. **Document ViewSet Actions:** Properly document DRF ViewSet URL patterns
5. **Implement Audit Log:** Either implement the audit log functionality or update documentation
6. **Add Authentication Details:** Document the custom JWT cookie authentication
7. **Complete Query Parameters:** Document all available filters and parameters
8. **Version the API:** Consider implementing API versioning as mentioned in docs

## Conclusion

The API documentation appears to be aspirational in some areas, documenting features that haven't been implemented yet (like audit logs and API logout). It also contains several inaccuracies in endpoint URLs and response formats. A comprehensive review and update of the documentation is recommended to align it with the actual implementation.