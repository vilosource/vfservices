# Missing API Endpoints Analysis

## Current State Analysis

After reviewing the implementation, I can confirm the following missing API endpoints:

### 1. API Logout Endpoint ❌
- **Current State**: Only web-based logout at `/logout/` exists
- **What's Missing**: No REST API endpoint for logout (e.g., `POST /api/logout/`)
- **Impact**: API clients cannot properly invalidate JWT tokens programmatically

### 2. User Attributes Management API ❌
- **Current State**: 
  - UserAttribute model exists in the database
  - AttributeService class exists with get/set methods
  - No REST API endpoints exposed for CRUD operations
- **What's Missing**:
  - `GET /api/admin/users/{id}/attributes/` - List user attributes
  - `POST /api/admin/users/{id}/attributes/` - Create/update attribute
  - `DELETE /api/admin/users/{id}/attributes/{attribute_name}/` - Delete attribute
  - `GET /api/admin/attributes/` - List all attribute definitions
  - `POST /api/admin/attributes/` - Define new attributes
- **Impact**: Cannot manage user attributes via API, limiting ABAC capabilities

## Documentation Updates

The current documentation in `/docs/api.md` accurately reflects what's implemented:
- Line 35 explicitly states: "No API logout endpoint exists"
- The bulk assignment endpoint documentation was incorrect (uses `user_id` not `username`)
- No user attributes endpoints are documented (correctly, as they don't exist)

## Implementation Plan

### Phase 1: API Logout Endpoint (Priority: High)

**Endpoint**: `POST /api/logout/`

**Implementation**:
1. Create `LogoutAPIView` in `views.py`
2. Clear JWT cookie (if present)
3. Optionally blacklist JWT token (requires token blacklist implementation)
4. Return success response

**Code Location**: `/identity_app/views.py`

```python
class LogoutAPIView(APIView):
    """API endpoint for logout."""
    authentication_classes = [JWTCookieAuthentication]
    
    def post(self, request):
        response = Response({"detail": "Logged out successfully"})
        response.delete_cookie('jwt', domain=settings.SSO_COOKIE_DOMAIN)
        
        # Optional: Add token to blacklist
        # BlacklistService.add_token(request.auth)
        
        return response
```

### Phase 2: User Attributes Management API (Priority: High)

#### 2.1 User-Specific Attribute Endpoints

**Base**: `/api/admin/users/{user_id}/attributes/`

**Endpoints**:
1. `GET /api/admin/users/{user_id}/attributes/` - List all attributes for a user
2. `GET /api/admin/users/{user_id}/attributes/{attribute_name}/` - Get specific attribute
3. `POST /api/admin/users/{user_id}/attributes/` - Create/update attribute
4. `DELETE /api/admin/users/{user_id}/attributes/{attribute_name}/` - Delete attribute

**Implementation**:
- Create `UserAttributeViewSet` as a nested viewset under UserViewSet
- Use `@action` decorators on UserViewSet for cleaner URLs

#### 2.2 Attribute Definition Endpoints

**Base**: `/api/admin/attributes/`

**Endpoints**:
1. `GET /api/admin/attributes/` - List all attribute definitions
2. `POST /api/admin/attributes/` - Create new attribute definition
3. `GET /api/admin/attributes/{id}/` - Get attribute definition details
4. `PUT /api/admin/attributes/{id}/` - Update attribute definition
5. `DELETE /api/admin/attributes/{id}/` - Delete attribute definition

**Implementation**:
- Create `ServiceAttributeViewSet` for managing attribute definitions
- Include validation for attribute types and default values

### Phase 3: Enhanced Features (Priority: Medium)

1. **Bulk Attribute Operations**:
   - `POST /api/admin/bulk/set-attributes/` - Set attributes for multiple users

2. **Attribute Audit Trail**:
   - Track who changed attributes and when
   - Include in audit log endpoint

3. **Attribute Validation**:
   - Validate attribute values against their defined types
   - Enforce required attributes per service

## Implementation Timeline

1. **Week 1**: API Logout endpoint
   - Implementation: 2 hours
   - Testing: 1 hour
   - Documentation: 30 minutes

2. **Week 2**: User Attributes API
   - Basic CRUD endpoints: 4 hours
   - Attribute definitions API: 3 hours
   - Testing: 2 hours
   - Documentation: 1 hour

3. **Week 3**: Enhanced Features
   - Bulk operations: 2 hours
   - Validation enhancements: 2 hours
   - Testing and documentation: 2 hours

## Security Considerations

1. **API Logout**:
   - Consider implementing JWT blacklisting for true logout
   - Clear both cookies and require token invalidation

2. **Attributes API**:
   - Ensure only `identity_admin` can manage attributes
   - Validate attribute types to prevent injection
   - Audit all attribute changes
   - Consider attribute-level permissions in the future

## Testing Requirements

1. **API Logout Tests**:
   - Test cookie clearing
   - Test with/without valid JWT
   - Test response format

2. **Attributes API Tests**:
   - CRUD operations for user attributes
   - Attribute definition management
   - Permission checks
   - Type validation
   - Bulk operations

## Migration Notes

- No database migrations needed (models already exist)
- Existing AttributeService can be reused
- Need to add serializers for UserAttribute and ServiceAttribute