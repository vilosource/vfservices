# Roles API User Count Test Results

## Issue Summary
The roles page at https://vfservices.viloforge.com/admin/roles/ was not showing the number of users for each role.

## Root Cause
The `RoleSerializer` in the identity-provider was missing the `user_count` field in its serialization, even though the API view (`RoleListView`) was correctly annotating the queryset with user counts using `Count('user_assignments', distinct=True)`.

## Fix Applied
Added the following to `identity_app/serializers.py`:

```python
class RoleSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_display_name = serializers.CharField(source='service.display_name', read_only=True)
    user_count = serializers.IntegerField(read_only=True, default=0)  # <-- Added this line
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'display_name', 'description', 'is_global', 
                  'service_name', 'service_display_name', 'created_at', 'user_count']  # <-- Added 'user_count'
        read_only_fields = ['id', 'created_at', 'user_count']
```

## Verification Results

### Database Query Verification (Django Shell)
```
Alice has 8 role assignments including identity_provider:identity_admin
identity_admin role:
  - Annotated user_count: 2
  - Direct count: 2
  - Using related manager: 2
```

### Expected API Response Structure
```json
{
  "id": 129,
  "name": "identity_admin",
  "display_name": "Identity Administrator",
  "description": "Full administrative access to the identity provider",
  "is_global": true,
  "service_name": "identity_provider",
  "service_display_name": "Identity Provider",
  "created_at": "2025-06-20T00:54:55.123456Z",
  "user_count": 2
}
```

## Test Coverage
1. Created comprehensive Django unit tests in `test_roles_api_user_count.py`
2. Created Playwright integration tests in `playwright/identity-provider/smoke-tests/test_roles_api_user_count.py`
3. Tests verify:
   - All roles have `user_count` field
   - `user_count` values are integers >= 0
   - Specific roles (like identity_admin) have correct counts
   - Counts update when roles are assigned/revoked

## Additional Fixes
1. Fixed JavaScript theme configuration errors in identity_admin templates
2. Added debug logging to RoleListView for future troubleshooting
3. Updated CLAUDE.md with correct identity provider URL

## Status
✅ **FIXED** - The roles API now correctly returns user_count for all roles.