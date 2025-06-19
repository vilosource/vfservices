# Redis Cache Fix Summary

## Changes Implemented

### 1. Extended Redis TTL (Time To Live)
- **Previous**: 300 seconds (5 minutes)
- **New**: 86400 seconds (24 hours) by default
- **Configurable**: via `RBAC_ABAC_CACHE_TTL` environment variable

### 2. Automatic Cache Refresh
- When cache miss occurs, system automatically fetches fresh data from identity provider
- Prevents users from losing access when cache expires
- Controlled by `auto_refresh` parameter (default: True)

### 3. Manual Cache Refresh API
- New endpoint: `POST /api/refresh-user-cache/`
- Allows on-demand cache refresh for specific users
- Useful after role/permission changes

## Files Modified

### Common RBAC-ABAC Package
- `/common/rbac_abac/redis_client.py`:
  - Changed default TTL from 300 to 86400 seconds
  - Added `auto_refresh` parameter to `get_user_attributes()`
  - Added `refresh_user_attributes_from_identity_provider()` function

### Identity Provider
- `/identity-provider/identity_app/views.py`:
  - Added `RefreshUserCacheView` class
- `/identity-provider/identity_app/urls.py`:
  - Added `/api/refresh-user-cache/` endpoint
- `/identity-provider/main/settings.py`:
  - Added `RBAC_ABAC_CACHE_TTL` configuration

### Service APIs
- `/billing-api/main/settings.py`:
  - Added `RBAC_ABAC_CACHE_TTL` configuration
  - Added `IDENTITY_PROVIDER_URL` configuration
- `/inventory-api/main/settings.py`:
  - Added `RBAC_ABAC_CACHE_TTL` configuration
  - Added `IDENTITY_PROVIDER_URL` configuration

### Docker Configuration
- `/docker-compose.yml`:
  - Added `RBAC_ABAC_CACHE_TTL` environment variable to all services
  - Added `IDENTITY_PROVIDER_URL` environment variable to API services

## New Files Created
- `/test_redis_cache_refresh.py`: Test script to verify the implementation
- `/docs/REDIS-CACHE-REFRESH.md`: Detailed documentation
- `/REDIS-CACHE-FIX-SUMMARY.md`: This summary file

## Usage

### Setting Custom TTL
Add to your `.env` file or export:
```bash
export RBAC_ABAC_CACHE_TTL=172800  # 48 hours
```

### Testing the Fix
```bash
python test_redis_cache_refresh.py
```

### Manual Cache Refresh
```bash
curl -X POST http://identity-provider:8000/api/refresh-user-cache/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "service_name": "billing_api"}'
```

## Benefits
1. **Stability**: Users no longer lose access every 5 minutes
2. **Performance**: 24-hour cache reduces database queries
3. **Flexibility**: Configurable TTL per deployment
4. **Reliability**: Auto-refresh ensures continuous service
5. **Control**: Manual refresh for immediate updates