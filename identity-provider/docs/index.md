# Identity Provider Documentation

Welcome to the Identity Provider documentation. This service is the core authentication and authorization system for the VFServices ecosystem.

## Overview

The Identity Provider service manages:
- User authentication (login/logout)
- User account management
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC)
- Service registration and permissions
- Audit logging

## Documentation Contents

### [API Documentation](./api.md)
Complete REST API reference including:
- Authentication endpoints
- User management APIs
- Role and permission management
- Service registration
- Audit log access

### [Admin API Testing](./admin-api-testing.md)
Comprehensive guide to testing the admin APIs:
- Testing architecture and approach
- Common issues and solutions
- Running tests locally
- Debugging failed tests

### [Logging Configuration](./Logging.md)
Details about the logging system:
- Log levels and configuration
- Structured logging format
- Integration with monitoring systems

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL database
- Redis (for caching)

### Running the Service

1. Start all services:
```bash
docker compose up -d
```

2. Run migrations:
```bash
docker compose exec identity-provider python manage.py migrate
```

3. Create admin user:
```bash
docker compose exec identity-provider python manage.py setup_admin_test_user
```

4. Access the service:
- Web UI: https://identity.vfservices.viloforge.com
- API: https://identity.vfservices.viloforge.com/api/

### Default Credentials
- Username: `admin`
- Password: `admin123`

## Architecture

### Components

1. **Django Application**: Core web framework
2. **PostgreSQL Database**: User and permission storage
3. **Redis Cache**: Performance optimization for user attributes
4. **JWT Middleware**: Token-based authentication
5. **RBAC/ABAC System**: Fine-grained access control

### Key Features

- **Single Sign-On (SSO)**: Shared authentication across all VFServices
- **Multi-Service Support**: Each service can define its own roles and permissions
- **Attribute-Based Policies**: Beyond roles, support for complex attribute-based rules
- **Audit Trail**: Complete logging of all administrative actions
- **Cache Invalidation**: Real-time permission updates across services

## Security

### Authentication Methods
1. **Cookie-based JWT**: For web applications
2. **Bearer Token**: For API clients
3. **Session-based**: For Django admin interface

### Permission Model
- **Roles**: Named collections of permissions (e.g., `identity_admin`, `billing_viewer`)
- **Services**: Each service defines its own roles
- **Global vs Scoped**: Roles can be global or scoped to specific resources
- **Expiration**: Roles can have optional expiration dates

### Best Practices
1. Use HTTPS for all communications
2. Implement proper CORS policies
3. Regular security audits
4. Monitor audit logs for suspicious activity
5. Rotate JWT secrets periodically

## Integration Guide

### For New Services

1. Define your service manifest:
```json
{
    "service": {
        "name": "your_service",
        "display_name": "Your Service",
        "description": "Service description"
    },
    "roles": [
        {
            "name": "service_admin",
            "display_name": "Administrator",
            "description": "Full access",
            "is_global": true
        }
    ]
}
```

2. Register with Identity Provider:
```bash
curl -X POST https://identity.vfservices.viloforge.com/api/register-manifest/ \
  -H "Content-Type: application/json" \
  -d @manifest.json
```

3. Use JWT middleware in your service:
```python
from common.jwt_auth.middleware import JWTAuthenticationMiddleware

MIDDLEWARE = [
    # ... other middleware
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',
]
```

### For Frontend Applications

1. Implement login flow:
```javascript
// Login
const response = await fetch('https://identity.vfservices.viloforge.com/api/login/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
});
const { token } = await response.json();

// Use token for subsequent requests
const apiResponse = await fetch('https://your-api.vfservices.viloforge.com/endpoint', {
    headers: { 'Authorization': `Bearer ${token}` }
});
```

2. Handle authentication errors:
- 401: Token expired or invalid
- 403: Insufficient permissions

## Troubleshooting

### Common Issues

1. **CSRF Token Errors**
   - Use Bearer token authentication for APIs
   - Custom authentication class bypasses CSRF for API endpoints

2. **Permission Denied**
   - Verify user has required role
   - Check role hasn't expired
   - Ensure service is active

3. **Cache Inconsistency**
   - Redis cache automatically invalidates on changes
   - Manual cache clear: `docker compose exec redis redis-cli FLUSHALL`

4. **JWT Token Issues**
   - Tokens expire after configured time
   - Refresh by re-authenticating
   - Check JWT_SECRET matches across services

### Debug Mode

Enable detailed logging:
```python
# In settings.py
LOGGING['root']['level'] = 'DEBUG'
```

View logs:
```bash
docker compose logs -f identity-provider
```

## Support

For issues or questions:
1. Check the [troubleshooting guide](#troubleshooting)
2. Review [API documentation](./api.md)
3. Check service logs
4. Contact the development team

## Related Documentation

- [VFServices Overview](../../README.md)
- [RBAC-ABAC System](../../docs/RBAC-ABAC.md)
- [Development Guide](../../docs/development.md)