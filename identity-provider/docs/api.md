# Identity Provider API Documentation

## Overview

The Identity Provider service manages authentication, user accounts, roles, and permissions for the VFServices ecosystem. It provides both traditional web-based authentication and REST API endpoints for programmatic access.

## Base URL

- Development: `https://identity.vfservices.viloforge.com`
- Production: Configure as needed

## Authentication

The Identity Provider uses JWT (JSON Web Tokens) for authentication. Tokens can be passed either:
1. As cookies (for web applications) - Primary method for admin API
2. As Bearer tokens in the Authorization header (for API clients)

The admin API uses a custom `JWTCookieAuthentication` that works with JWT cookies without triggering CSRF checks.

### Web-Based Login/Logout

**Login Page**: `GET /login/`
- Displays login form
- Accepts optional `redirect_uri` parameter
- On successful login, sets httpOnly JWT cookie and redirects

**Login Form Submission**: `POST /login/`
- Form data: `username`, `password`, `redirect_uri`
- Sets JWT cookie with domain-wide SSO
- Redirects to `redirect_uri` or default URL

**Logout**: `GET /logout/`
- Clears JWT cookie
- Redirects to `settings.DEFAULT_REDIRECT_URL`
- No API logout endpoint exists

### API Login

**Endpoint**: `POST /api/login/`

**Request Body**:
```json
{
    "username": "string",
    "password": "string"
}
```

**Response**:
```json
{
    "token": "jwt_token_string"
}
```

**Example**:
```bash
curl -X POST https://identity.vfservices.viloforge.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## API Information

### Get API Info

**Endpoint**: `GET /api/`

**Response**: Returns available endpoints and API information

### Health Check

**Endpoint**: `GET /api/status/`

**Response**:
```json
{
    "status": "healthy",
    "service": "identity-provider",
    "version": "1.0.0",
    "timestamp": "2024-01-20T12:00:00Z"
}
```

## User Profile

### Get Current User Profile

**Endpoint**: `GET /api/profile/`

**Headers**: Requires authentication (JWT cookie or Bearer token)

**Response**:
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "roles": [
        {
            "role_name": "identity_admin",
            "service_name": "identity_provider",
            "is_active": true
        }
    ],
    "timestamp": "2024-01-20T12:00:00Z"
}
```

## Service Registration

### Register Service Manifest

**Endpoint**: `POST /api/services/register/`

**Request Body**:
```json
{
    "service": "new_service",
    "display_name": "New Service",
    "description": "Description of the service",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "service_admin",
            "display_name": "Service Administrator",
            "description": "Full admin access to the service",
            "is_global": true
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department",
            "type": "string",
            "is_required": false,
            "default_value": null
        }
    ]
}
```

**Response**: 200 OK
```json
{
    "service": "new_service",
    "version": 1,
    "status": "registered",
    "roles_created": 1,
    "roles_updated": 0,
    "attributes_created": 1,
    "attributes_updated": 0
}
```

## Cache Management

### Refresh User Cache

**Endpoint**: `POST /api/refresh-user-cache/`

**Request Body**:
```json
{
    "user_id": 1,
    "service_name": "billing-api"
}
```

**Response**: 200 OK
```json
{
    "detail": "Cache refreshed successfully"
}
```

## Admin API

All admin endpoints require the `identity_admin` role and use JWT cookie authentication.

### Users

#### List Users

**Endpoint**: `GET /api/admin/users/`

**Query Parameters**:
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 50, max: 100)
- `search` - Search by username, email, first/last name
- `is_active` - Filter by active status (true/false)
- `has_role` - Filter by role name
- `service` - Filter by service name
- `ordering` - Order by field (username, email, date_joined, last_login, is_active)

**Response**:
```json
{
    "count": 100,
    "next": "http://example.com/api/admin/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "is_active": true,
            "is_staff": false,
            "is_superuser": false,
            "date_joined": "2024-01-01T00:00:00Z",
            "last_login": "2024-01-20T12:00:00Z",
            "roles_count": 1
        }
    ]
}
```

#### Get User Details

**Endpoint**: `GET /api/admin/users/{id}/`

**Response**:
```json
{
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "is_active": true,
    "is_staff": false,
    "is_superuser": false,
    "date_joined": "2024-01-01T00:00:00Z",
    "last_login": "2024-01-20T12:00:00Z",
    "groups": [],
    "user_permissions": [],
    "roles": [
        {
            "id": 1,
            "role": {
                "id": 1,
                "name": "identity_admin",
                "display_name": "Identity Administrator",
                "description": "Full administrative access",
                "is_global": true
            },
            "service": {
                "id": 1,
                "name": "identity_provider",
                "display_name": "Identity Provider"
            },
            "granted_at": "2024-01-01T00:00:00Z",
            "granted_by": {
                "id": 1,
                "username": "system"
            },
            "expires_at": null,
            "is_active": true
        }
    ]
}
```

#### Create User

**Endpoint**: `POST /api/admin/users/`

**Request Body**:
```json
{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "first_name": "New",
    "last_name": "User",
    "is_active": true,
    "initial_roles": [
        {
            "role_name": "billing_viewer",
            "service_name": "billing_api"
        }
    ]
}
```

**Response**: 201 Created with user details

#### Update User

**Endpoint**: `PATCH /api/admin/users/{id}/`

**Request Body** (partial update):
```json
{
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "Name"
}
```

**Response**: 200 OK with updated user details

#### Deactivate User

**Endpoint**: `DELETE /api/admin/users/{id}/`

**Note**: Performs soft delete (sets is_active=False). Cannot delete superuser accounts.

**Response**: 204 No Content

#### Set User Password

**Endpoint**: `POST /api/admin/users/{id}/set_password/`

**Request Body**:
```json
{
    "password": "NewSecurePass123!",
    "force_change": false
}
```

**Response**: 200 OK
```json
{
    "status": "Password set successfully"
}
```

### User Roles

#### List User's Roles

**Endpoint**: `GET /api/admin/users/{id}/roles/`

**Response**:
```json
[
    {
        "id": 1,
        "role": {
            "id": 1,
            "name": "identity_admin",
            "display_name": "Identity Administrator",
            "description": "Full administrative access",
            "is_global": true
        },
        "service": {
            "id": 1,
            "name": "identity_provider",
            "display_name": "Identity Provider"
        },
        "granted_at": "2024-01-01T00:00:00Z",
        "granted_by": {
            "id": 1,
            "username": "admin"
        },
        "expires_at": null,
        "is_active": true
    }
]
```

#### Assign Role to User

**Endpoint**: `POST /api/admin/users/{id}/roles/`

**Request Body**:
```json
{
    "role_name": "billing_admin",
    "service_name": "billing_api",
    "expires_at": "2024-12-31T23:59:59Z",
    "reason": "Temporary access for Q4 audit"
}
```

**Response**: 201 Created with role assignment details

#### Revoke Role from User

**Endpoint**: `DELETE /api/admin/users/{id}/roles/{role_id}/`

**Response**: 204 No Content

### Services and Roles

#### List All Services

**Endpoint**: `GET /api/admin/services/`

**Response**:
```json
[
    {
        "id": 1,
        "name": "identity_provider",
        "display_name": "Identity Provider",
        "description": "Core identity and access management service",
        "is_active": true,
        "manifest_version": 1,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z"
    }
]
```

#### List All Roles

**Endpoint**: `GET /api/admin/roles/`

**Query Parameters**:
- `service` - Filter by service name
- `is_global` - Filter by global status (true/false)

**Response**:
```json
[
    {
        "id": 1,
        "name": "identity_admin",
        "display_name": "Identity Administrator",
        "description": "Full administrative access to identity provider",
        "is_global": true,
        "service": {
            "id": 1,
            "name": "identity_provider",
            "display_name": "Identity Provider"
        }
    }
]
```

### Bulk Operations

#### Bulk Assign Roles

**Endpoint**: `POST /api/admin/bulk/assign-roles/`

**Request Body**:
```json
{
    "assignments": [
        {
            "username": "user1",
            "role_name": "billing_viewer",
            "service_name": "billing_api"
        },
        {
            "username": "user2",
            "role_name": "costs_admin",
            "service_name": "azure_costs"
        }
    ],
    "expires_at": "2024-12-31T23:59:59Z",
    "reason": "Bulk assignment for new team"
}
```

**Response**:
```json
{
    "created": [
        {
            "user": "user1",
            "role": "billing_viewer",
            "id": 123
        }
    ],
    "errors": [
        {
            "user": "user2",
            "role": "costs_admin",
            "error": "User not found"
        }
    ],
    "total": 2,
    "success": 1
}
```

**Status Code**: 201 if any assignments succeed, 400 if all fail

### Audit Log

#### View Audit Log

**Endpoint**: `GET /api/admin/audit-log/`

**Note**: Currently returns empty results (not yet implemented)

**Response**:
```json
{
    "results": [],
    "count": 0
}
```

## Error Responses

All endpoints return standard HTTP status codes and error messages:

### 400 Bad Request
```json
{
    "field_name": ["Error message for this field"],
    "non_field_errors": ["General error message"]
}
```

### 401 Unauthorized
```json
{
    "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
    "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
    "detail": "Not found."
}
```

### 500 Internal Server Error
```json
{
    "detail": "Internal server error. Please try again later."
}
```

## Pagination

Admin API list endpoints use standard pagination:
- Default page size: 50
- Maximum page size: 100
- Query parameter: `page_size`
- Response includes `count`, `next`, and `previous` fields

## Rate Limiting

API endpoints are not currently rate-limited but this may be added in the future. Plan for reasonable request rates.

## Versioning

The API is currently at version 1. Future versions will be indicated in the URL path (e.g., `/api/v2/`).

## CORS

Cross-Origin Resource Sharing (CORS) is configured to allow requests from authorized domains. The identity provider includes a CORS discovery system that automatically detects and validates allowed origins.

## Interactive API Documentation

- **Swagger UI**: Available at `/api/docs/`
- **ReDoc**: Available at `/api/redoc/`

These provide interactive API exploration and testing capabilities.