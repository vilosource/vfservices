# Identity Provider API Documentation

## Overview

The Identity Provider service manages authentication, user accounts, roles, and permissions for the VFServices ecosystem. It provides both traditional web-based authentication and REST API endpoints for programmatic access.

## Base URL

- Development: `https://identity.vfservices.viloforge.com`
- Production: Configure as needed

## Authentication

The Identity Provider uses JWT (JSON Web Tokens) for authentication. Tokens can be passed either:
1. As cookies (for web applications)
2. As Bearer tokens in the Authorization header (for API clients)

### Login

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

**Example**:
```bash
curl -X POST https://identity.vfservices.viloforge.com/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Logout

**Endpoint**: `POST /api/logout/`

**Headers**: Requires authentication

**Response**: 200 OK with empty body

## User Profile

### Get Current User Profile

**Endpoint**: `GET /api/profile/`

**Headers**: Requires authentication

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
    ]
}
```

## Admin API

All admin endpoints require the `identity_admin` role.

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
- `ordering` - Order by field (username, email, date_joined, last_login)

**Response**:
```json
{
    "count": 100,
    "next": "https://identity.vfservices.viloforge.com/api/admin/users/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "is_active": true,
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
    "roles": [
        {
            "id": 1,
            "role_name": "identity_admin",
            "role_display_name": "Identity Administrator",
            "service_name": "identity_provider",
            "service_display_name": "Identity Provider",
            "granted_at": "2024-01-01T00:00:00Z",
            "granted_by_username": "system",
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

**Endpoint**: `PUT /api/admin/users/{id}/`

**Request Body**:
```json
{
    "email": "updated@example.com",
    "first_name": "Updated",
    "last_name": "Name",
    "is_active": true
}
```

**Response**: 200 OK with updated user details

#### Deactivate User

**Endpoint**: `DELETE /api/admin/users/{id}/`

**Response**: 200 OK
```json
{
    "status": "User deactivated successfully"
}
```

#### Set User Password

**Endpoint**: `POST /api/admin/users/{id}/set-password/`

**Request Body**:
```json
{
    "password": "NewSecurePass123!"
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
        "role_name": "identity_admin",
        "role_display_name": "Identity Administrator",
        "service_name": "identity_provider",
        "service_display_name": "Identity Provider",
        "granted_at": "2024-01-01T00:00:00Z",
        "granted_by_username": "system",
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
    "expires_at": "2024-12-31T23:59:59Z",  // Optional
    "reason": "Temporary access for Q4 audit"  // Optional
}
```

**Response**: 201 Created with role details

#### Revoke Role from User

**Endpoint**: `DELETE /api/admin/users/{id}/roles/{role_id}/`

**Request Body**:
```json
{
    "reason": "No longer needed"  // Optional
}
```

**Response**: 200 OK
```json
{
    "status": "Role revoked successfully"
}
```

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
        "manifest_version": "1.0",
        "created_at": "2024-01-01T00:00:00Z"
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
        "service_name": "identity_provider",
        "service_display_name": "Identity Provider",
        "is_global": true
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
    "expires_at": "2024-12-31T23:59:59Z",  // Optional, applies to all
    "reason": "Bulk assignment for new team"  // Optional
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

### Audit Log

#### View Audit Log

**Endpoint**: `GET /api/admin/audit-log/`

**Query Parameters**:
- `user` - Filter by user ID
- `action` - Filter by action type
- `start_date` - Filter by date range start
- `end_date` - Filter by date range end
- `page` - Page number
- `page_size` - Results per page

**Response**:
```json
{
    "count": 50,
    "next": "...",
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": "admin",
            "action": "user_created",
            "resource_type": "user",
            "resource_id": "123",
            "timestamp": "2024-01-20T12:00:00Z",
            "changes": {
                "username": "newuser",
                "email": "newuser@example.com"
            },
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0..."
        }
    ]
}
```

## Service Registration

Services can register their RBAC manifests with the Identity Provider.

### Register Service Manifest

**Endpoint**: `POST /api/register-manifest/`

**Request Body**:
```json
{
    "service": {
        "name": "new_service",
        "display_name": "New Service",
        "description": "Description of the service"
    },
    "version": "1.0",
    "roles": [
        {
            "name": "service_admin",
            "display_name": "Service Administrator",
            "description": "Full admin access to the service",
            "is_global": true
        },
        {
            "name": "service_viewer",
            "display_name": "Service Viewer",
            "description": "Read-only access to the service",
            "is_global": false
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department",
            "type": "string",
            "required": false,
            "default": null
        }
    ]
}
```

**Response**: 201 Created
```json
{
    "service": "new_service",
    "version": 1,
    "registered_at": "2024-01-20T12:00:00Z",
    "is_active": true
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

## Rate Limiting

API endpoints are not currently rate-limited but this may be added in the future. Plan for reasonable request rates.

## Versioning

The API is currently at version 1. Future versions will be indicated in the URL path (e.g., `/api/v2/`).

## CORS

Cross-Origin Resource Sharing (CORS) is configured to allow requests from authorized domains. Ensure your application domain is whitelisted in production.