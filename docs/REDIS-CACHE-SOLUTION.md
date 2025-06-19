# Redis Cache Solution for RBAC-ABAC

## Problem
The Redis cache was expiring after 5 minutes, causing users to lose their permissions and receive 403 errors when accessing API endpoints.

## Solution Implemented

### 1. Extended Cache TTL
The cache TTL has been extended from 300 seconds (5 minutes) to **86400 seconds (24 hours)**.

**Location**: `/common/rbac_abac/redis_client.py` line 41
```python
self.ttl = ttl or getattr(settings, 'RBAC_ABAC_CACHE_TTL', 86400)
```

### 2. Auto-Refresh on Cache Miss
The `get_user_attributes()` function now includes automatic refresh functionality:

**Location**: `/common/rbac_abac/redis_client.py` lines 203-224
```python
def get_user_attributes(user_id: int, service_name: str, auto_refresh: bool = True) -> Optional[UserAttributes]:
    client = get_redis_client()
    
    # Try to get from cache first
    attrs = client.get_user_attributes(user_id, service_name)
    
    # If not found and auto_refresh is enabled, try to refresh from identity provider
    if attrs is None and auto_refresh:
        attrs = refresh_user_attributes_from_identity_provider(user_id, service_name)
    
    return attrs
```

### 3. Manual Cache Refresh
A management command is available to manually refresh the cache for all demo users:

```bash
docker exec vfservices-identity-provider-1 python manage.py refresh_demo_cache
```

### 4. API Endpoint for Cache Refresh
The identity provider exposes an endpoint for programmatic cache refresh:

**Endpoint**: `POST /api/refresh-user-cache/`
**Parameters**:
- `user_id`: The user's ID
- `service_name`: The service name (e.g., 'billing_api', 'inventory_api')

## How It Works

1. **Normal Operation**: When a service checks user permissions, it first checks Redis cache (24-hour TTL)
2. **Cache Miss**: If cache is empty, the system automatically fetches fresh data from the identity provider
3. **Auto-Population**: Fresh data is stored in Redis with 24-hour TTL
4. **No User Impact**: Users experience seamless access without 403 errors

## Configuration

To customize the cache TTL, set the environment variable:
```bash
RBAC_ABAC_CACHE_TTL=86400  # seconds (default: 24 hours)
```

## Benefits

1. **Reduced Cache Misses**: 24-hour TTL vs 5 minutes dramatically reduces cache expiration issues
2. **Self-Healing**: Automatic refresh on cache miss ensures continuous service
3. **No Manual Intervention**: System recovers automatically from cache issues
4. **Performance**: Redis cache still provides fast permission checks
5. **Flexibility**: TTL can be configured based on security requirements

## Testing

To verify the cache is working:

1. Login as a demo user
2. Access protected endpoints
3. Check that permissions are granted
4. Wait for cache to expire (or flush Redis)
5. Access endpoints again - should still work due to auto-refresh

## Maintenance

- For immediate cache updates after permission changes, use the manual refresh command
- Monitor Redis memory usage as cache entries now persist longer
- Consider implementing a cache warm-up on service startup for critical users