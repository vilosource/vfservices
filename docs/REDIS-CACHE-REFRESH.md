# Redis Cache Refresh Mechanism

## Overview

This document describes the Redis cache refresh mechanism implemented for the RBAC-ABAC system to prevent users from losing access to API endpoints due to cache expiration.

## Problem Statement

The original implementation had a Redis TTL (Time To Live) of only 300 seconds (5 minutes), causing user permissions to expire frequently. This resulted in users losing access to API endpoints when their cached attributes expired.

## Solution

The solution implements three key improvements:

### 1. Extended Cache TTL

- **Default TTL**: Increased from 300 seconds (5 minutes) to 86400 seconds (24 hours)
- **Configurable**: Can be customized via the `RBAC_ABAC_CACHE_TTL` environment variable
- **Per-service**: Each service can have its own TTL configuration

### 2. Automatic Cache Refresh

When a cache miss occurs (attributes not found in Redis), the system automatically:

1. Makes an API call to the identity provider
2. Fetches fresh user attributes
3. Stores them in Redis with the configured TTL
4. Returns the attributes to the requesting service

### 3. Manual Cache Refresh API

A new API endpoint allows services to manually trigger cache refresh:

- **Endpoint**: `POST /api/refresh-user-cache/`
- **Purpose**: Refresh user attributes on-demand
- **Use cases**: After role changes, attribute updates, or debugging

## Configuration

### Environment Variables

```bash
# Cache TTL in seconds (default: 86400 = 24 hours)
RBAC_ABAC_CACHE_TTL=86400

# Identity provider URL (for automatic refresh)
IDENTITY_PROVIDER_URL=http://identity-provider:8000
```

### Django Settings

Each service should include these settings:

```python
# Service name for RBAC-ABAC
SERVICE_NAME = 'your_service_name'

# RBAC-ABAC Cache settings
RBAC_ABAC_CACHE_TTL = int(os.environ.get('RBAC_ABAC_CACHE_TTL', 86400))
IDENTITY_PROVIDER_URL = os.environ.get('IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')
```

## Implementation Details

### Redis Client Changes

The `RedisAttributeClient` class now:

- Uses a configurable TTL (default 24 hours)
- Supports automatic refresh on cache miss
- Provides health check capabilities

### Auto-Refresh Flow

1. Service requests user attributes via `get_user_attributes()`
2. If not found in Redis and `auto_refresh=True`:
   - Calls `refresh_user_attributes_from_identity_provider()`
   - Makes POST request to identity provider
   - Identity provider populates Redis
   - Returns refreshed attributes

### Manual Refresh Flow

1. Client sends POST to `/api/refresh-user-cache/` with:
   ```json
   {
     "user_id": 123,
     "service_name": "billing_api"
   }
   ```
2. Identity provider:
   - Fetches user roles and attributes from database
   - Builds `UserAttributes` object
   - Stores in Redis with configured TTL
   - Returns success/failure response

## Benefits

1. **Reduced Cache Misses**: 24-hour TTL significantly reduces expiration events
2. **Self-Healing**: Automatic refresh prevents service disruption
3. **Flexibility**: Manual refresh allows immediate updates when needed
4. **Performance**: Caching still provides fast attribute lookups
5. **Reliability**: Services continue functioning even if cache expires

## Monitoring

Monitor these metrics for cache health:

- Cache hit/miss ratio
- Auto-refresh frequency
- Manual refresh requests
- Redis connection failures
- Average attribute lookup time

## Testing

Run the test script to verify the implementation:

```bash
python test_redis_cache_refresh.py
```

This tests:
- Redis connectivity
- TTL configuration
- Automatic cache refresh
- Manual cache refresh

## Troubleshooting

### Common Issues

1. **Cache not refreshing automatically**
   - Check `IDENTITY_PROVIDER_URL` configuration
   - Verify network connectivity between services
   - Check identity provider logs for errors

2. **TTL not applying correctly**
   - Verify `RBAC_ABAC_CACHE_TTL` environment variable
   - Check service settings configuration
   - Ensure Redis client is using updated code

3. **Permission denied after refresh**
   - Verify user has active roles in identity provider
   - Check service manifest is registered
   - Ensure user attributes are properly configured

## Future Improvements

1. **Cache Warming**: Pre-populate cache for active users
2. **Sliding Expiration**: Extend TTL on each access
3. **Partial Refresh**: Update specific attributes without full reload
4. **Cache Metrics**: Built-in monitoring and alerting
5. **Distributed Cache**: Redis cluster for high availability