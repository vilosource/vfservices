# VFAdmin Specification

## 1. Executive Summary

VFAdmin is a user and role management system for the VF Services platform. It consists of two components:
1. **Identity Provider API Extensions** - RESTful API endpoints for user/role management
2. **VFAdmin Django App** - Reusable frontend that can be embedded in any Django project

The system enables administrators to manage users, assign roles, and control access across all VF Services through a unified interface.

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  CIELO Website  │     │     Website     │     │  Future Django  │
│   (Django)      │     │    (Django)     │     │    Projects     │
├─────────────────┤     ├─────────────────┤     ├─────────────────┤
│  VFAdmin App    │     │  VFAdmin App    │     │  VFAdmin App    │
│  (Frontend)     │     │  (Frontend)     │     │  (Frontend)     │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                         │
         │         API Calls     │                         │
         │         (JWT Auth)    │                         │
         └───────────────────────┴─────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   Identity Provider    │
                    │    (Django + DRF)      │
                    ├────────────────────────┤
                    │  Admin API Endpoints   │
                    │  - User Management     │
                    │  - Role Management     │
                    │  - Service Registry   │
                    └────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
            ┌──────────────┐         ┌──────────────┐
            │  PostgreSQL  │         │    Redis     │
            │   Database   │         │    Cache     │
            └──────────────┘         └──────────────┘
```

### 2.2 Component Responsibilities

#### Identity Provider API Extensions
- Expose RESTful endpoints for user and role management
- Handle authentication and authorization
- Validate data and enforce business rules
- Manage database transactions
- Invalidate Redis cache on changes
- Emit audit logs for all operations

#### VFAdmin Django App
- Provide reusable UI components
- Handle API communication with Identity Provider
- Render HTML templates
- Manage client-side state
- Display errors and success messages
- No direct database access

## 3. Functional Requirements

### 3.1 User Management

#### 3.1.1 List Users
- **Endpoint**: `GET /api/admin/users/`
- **Features**:
  - Pagination (default 50 per page)
  - Search by username, email, first name, last name
  - Filter by:
    - Active/inactive status
    - Date joined range
    - Last login range
    - Has specific role
    - Service assignment
  - Sort by any field
  - Include role count in response

#### 3.1.2 View User Details
- **Endpoint**: `GET /api/admin/users/{id}/`
- **Response includes**:
  - All Django User model fields
  - Assigned roles with expiration dates
  - Service associations
  - Last login information
  - Account status
  - Future: User attributes

#### 3.1.3 Create User
- **Endpoint**: `POST /api/admin/users/`
- **Required fields**:
  - Username (unique)
  - Email (unique)
  - Password
- **Optional fields**:
  - First name
  - Last name
  - Is active (default: true)
  - Initial roles
- **Business rules**:
  - Username must be alphanumeric + underscore/hyphen
  - Email must be valid format
  - Password must meet security requirements
  - Cannot create superuser via API

#### 3.1.4 Update User
- **Endpoint**: `PATCH /api/admin/users/{id}/`
- **Editable fields**:
  - Email
  - First name
  - Last name
  - Is active
- **Non-editable via API**:
  - Username (security consideration)
  - Password (use separate endpoint)
  - Is superuser
  - Is staff

#### 3.1.5 Delete User
- **Endpoint**: `DELETE /api/admin/users/{id}/`
- **Behavior**:
  - Soft delete (set is_active=False)
  - Preserve audit trail
  - Revoke all active sessions
  - Clear Redis cache

#### 3.1.6 Change Password
- **Endpoint**: `POST /api/admin/users/{id}/set-password/`
- **Options**:
  - Set specific password
  - Generate random password
  - Force password change on next login
  - Send password reset email

### 3.2 Role Management

#### 3.2.1 List User Roles
- **Endpoint**: `GET /api/admin/users/{id}/roles/`
- **Response includes**:
  - Role name and display name
  - Service information
  - Assigned date
  - Assigned by (user)
  - Expiration date
  - Is active

#### 3.2.2 Assign Role
- **Endpoint**: `POST /api/admin/users/{id}/roles/`
- **Request body**:
  ```json
  {
    "role_name": "billing_admin",
    "service_name": "billing_api",
    "expires_at": "2025-12-31T23:59:59Z"  // optional
  }
  ```
- **Business rules**:
  - Role must exist
  - Service must be registered
  - Cannot assign expired role
  - Check for duplicate assignments

#### 3.2.3 Update Role Assignment
- **Endpoint**: `PATCH /api/admin/users/{id}/roles/{role_id}/`
- **Editable**:
  - Expiration date only
- **Use cases**:
  - Extend role assignment
  - Set expiration date

#### 3.2.4 Revoke Role
- **Endpoint**: `DELETE /api/admin/users/{id}/roles/{role_id}/`
- **Behavior**:
  - Soft delete with revoked_at timestamp
  - Clear Redis cache
  - Audit log entry

### 3.3 Service & Role Discovery

#### 3.3.1 List Services
- **Endpoint**: `GET /api/admin/services/`
- **Response includes**:
  - Service name and display name
  - Description
  - Registration date
  - Available roles
  - Active user count

#### 3.3.2 List Roles
- **Endpoint**: `GET /api/admin/roles/`
- **Query parameters**:
  - `service`: Filter by service
  - `is_global`: Filter global roles
- **Response includes**:
  - Role details
  - User count
  - Service association

### 3.4 Bulk Operations

#### 3.4.1 Bulk Create Users
- **Endpoint**: `POST /api/admin/users/bulk-create/`
- **Format**: JSON array or CSV upload
- **Features**:
  - Validation before processing
  - Transaction support
  - Error reporting per user
  - Optional email notifications

#### 3.4.2 Bulk Assign Roles
- **Endpoint**: `POST /api/admin/roles/bulk-assign/`
- **Use cases**:
  - Assign role to multiple users
  - Assign multiple roles to one user
  - Copy roles from template user

### 3.5 Audit & Monitoring

#### 3.5.1 Audit Log
- **Endpoint**: `GET /api/admin/audit-log/`
- **Tracked events**:
  - User created/updated/deleted
  - Role assigned/revoked
  - Password changed
  - Bulk operations
- **Includes**:
  - Actor (who made change)
  - Timestamp
  - IP address
  - Change details

## 4. Non-Functional Requirements

### 4.1 Security

#### Authentication
- All endpoints require JWT authentication
- JWT token must be valid and not expired
- User must have `identity_admin` role

#### Authorization
- Role-based access control
- Admin role required for all operations
- Future: Granular permissions (read-only admin, service-specific admin)

#### Data Protection
- Passwords never returned in API responses
- Sensitive operations logged
- Rate limiting on API endpoints
- CORS configuration for approved origins only

### 4.2 Performance

#### API Response Times
- List operations: < 200ms
- Single resource: < 100ms
- Create/Update: < 300ms
- Bulk operations: < 5s for 100 items

#### Caching Strategy
- Cache service and role lists (TTL: 1 hour)
- Invalidate user cache on any change
- Use ETags for conditional requests

### 4.3 Scalability

#### Database
- Indexed fields for search/filter
- Pagination required for all list endpoints
- Efficient queries with select_related/prefetch_related

#### API Design
- RESTful principles
- Stateless operations
- Horizontal scaling support

### 4.4 Reliability

#### Error Handling
- Consistent error response format
- Meaningful error messages
- HTTP status codes follow standards
- Validation errors include field details

#### Data Integrity
- Database transactions for multi-step operations
- Foreign key constraints
- Soft deletes preserve history

## 5. API Specification

### 5.1 Base Configuration
- **Base URL**: `https://identity.{domain}/api/admin/`
- **Authentication**: JWT Bearer token or cookie
- **Content-Type**: `application/json`
- **API Version**: v1 (in URL or header)

### 5.2 Common Response Format

#### Success Response
```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "meta": {
    "timestamp": "2024-01-20T10:30:00Z",
    "version": "1.0"
  }
}
```

#### Error Response
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "email": ["Email already exists"]
    }
  },
  "meta": {
    "timestamp": "2024-01-20T10:30:00Z",
    "request_id": "req_123456"
  }
}
```

#### Paginated Response
```json
{
  "status": "success",
  "data": {
    "results": [...],
    "pagination": {
      "count": 150,
      "page": 1,
      "page_size": 50,
      "total_pages": 3,
      "next": "https://api.example.com/users/?page=2",
      "previous": null
    }
  }
}
```

### 5.3 Endpoint Details

#### User Endpoints

##### List Users
```
GET /api/admin/users/
```

Query Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 50, max: 100)
- `search`: Search in username, email, names
- `is_active`: Filter by active status
- `has_role`: Filter by role name
- `service`: Filter by service assignment
- `ordering`: Sort field (prefix with - for descending)

Example:
```
GET /api/admin/users/?search=john&is_active=true&ordering=-date_joined
```

##### Create User
```
POST /api/admin/users/
```

Request Body:
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "initial_roles": [
    {
      "role_name": "billing_viewer",
      "service_name": "billing_api"
    }
  ]
}
```

##### Update User
```
PATCH /api/admin/users/{id}/
```

Request Body (partial update):
```json
{
  "email": "newemail@example.com",
  "is_active": false
}
```

#### Role Endpoints

##### Assign Role
```
POST /api/admin/users/{id}/roles/
```

Request Body:
```json
{
  "role_name": "costs_admin",
  "service_name": "azure_costs",
  "expires_at": "2025-12-31T23:59:59Z",
  "reason": "Quarterly access for cost analysis"
}
```

##### Bulk Assign Roles
```
POST /api/admin/roles/bulk-assign/
```

Request Body:
```json
{
  "assignments": [
    {
      "user_id": 1,
      "role_name": "viewer",
      "service_name": "billing_api"
    },
    {
      "user_id": 2,
      "role_name": "admin",
      "service_name": "azure_costs"
    }
  ],
  "expires_at": "2025-06-30T23:59:59Z"
}
```

## 6. VFAdmin Django App Specification

### 6.1 Installation

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps
    'vfadmin',
]

# VFAdmin configuration
VFADMIN_CONFIG = {
    'IDENTITY_PROVIDER_URL': 'https://identity.vfservices.com',
    'API_TIMEOUT': 30,
    'PAGE_SIZE': 50,
    'ENABLE_BULK_OPERATIONS': True,
    'THEME': 'auto',  # 'light', 'dark', 'auto'
}

# urls.py
urlpatterns = [
    path('admin/', include('vfadmin.urls')),
]
```

### 6.2 URL Structure

- `/admin/` - Dashboard
- `/admin/users/` - User list
- `/admin/users/create/` - Create user form
- `/admin/users/{id}/` - User detail/edit
- `/admin/users/{id}/roles/` - Manage user roles
- `/admin/roles/` - Role browser
- `/admin/services/` - Service browser
- `/admin/audit/` - Audit log

### 6.3 Templates Structure

```
vfadmin/
├── templates/
│   └── vfadmin/
│       ├── base.html
│       ├── dashboard.html
│       ├── users/
│       │   ├── list.html
│       │   ├── detail.html
│       │   ├── create.html
│       │   └── roles.html
│       ├── roles/
│       │   └── list.html
│       ├── services/
│       │   └── list.html
│       └── components/
│           ├── pagination.html
│           ├── search.html
│           └── messages.html
```

### 6.4 Static Files

```
vfadmin/
├── static/
│   └── vfadmin/
│       ├── css/
│       │   └── vfadmin.css
│       ├── js/
│       │   ├── api-client.js
│       │   ├── users.js
│       │   ├── roles.js
│       │   └── utils.js
│       └── img/
│           └── logo.png
```

### 6.5 JavaScript API Client

```javascript
// vfadmin/static/vfadmin/js/api-client.js
class VFAdminAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': this.getCSRFToken(),
        ...options.headers
      },
      credentials: 'include'
    });

    if (!response.ok) {
      throw new APIError(response);
    }

    return response.json();
  }

  // User methods
  async getUsers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    return this.request(`/users/?${queryString}`);
  }

  async createUser(userData) {
    return this.request('/users/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  // ... other methods
}
```

### 6.6 UI Components

#### User List Table
- Sortable columns
- Inline search
- Bulk selection
- Action buttons (edit, manage roles, deactivate)
- Status indicators (active, superuser, staff)

#### User Form
- Client-side validation
- Password strength indicator
- Role assignment widget
- Success/error messages
- Loading states

#### Role Assignment Modal
- Service dropdown
- Role dropdown (filtered by service)
- Expiration date picker
- Reason field
- Current roles display

### 6.7 Security Considerations

#### Frontend Security
- CSRF protection on all forms
- XSS prevention (escape all user content)
- Content Security Policy headers
- Secure cookie handling

#### API Communication
- Always use HTTPS
- Include CSRF token in headers
- Handle JWT expiration gracefully
- Sanitize all user inputs

## 7. Implementation Plan

### Phase 1: Identity Provider API (Week 1-2)
1. Design database schema changes
2. Implement user management endpoints
3. Implement role management endpoints
4. Add authentication/authorization
5. Write API tests

### Phase 2: VFAdmin Core (Week 3-4)
1. Create Django app structure
2. Implement API client
3. Create base templates
4. Implement user list and detail views
5. Add create/edit functionality

### Phase 3: Role Management UI (Week 5)
1. Implement role assignment UI
2. Add bulk operations
3. Create service/role browsers
4. Add search and filtering

### Phase 4: Polish & Testing (Week 6)
1. Add audit log viewer
2. Improve error handling
3. Add loading states
4. Write frontend tests
5. Documentation

### Phase 5: Integration (Week 7)
1. Install in CIELO website
2. Install in main website
3. Configure permissions
4. User acceptance testing
5. Deploy to production

## 8. Testing Strategy

### API Testing
- Unit tests for all endpoints
- Integration tests with database
- Permission tests (unauthorized access)
- Performance tests (load testing)
- API documentation tests

### Frontend Testing
- Unit tests for JavaScript modules
- Django view tests
- Template rendering tests
- Integration tests with API
- Cross-browser testing

### Security Testing
- Authentication bypass attempts
- Authorization boundary testing
- Input validation testing
- XSS and injection testing
- Session management testing

## 9. Documentation Requirements

### API Documentation
- OpenAPI/Swagger specification
- Authentication guide
- Example requests/responses
- Error code reference
- Rate limiting details

### Frontend Documentation
- Installation guide
- Configuration options
- Customization guide
- Template override examples
- JavaScript API reference

### User Documentation
- Administrator guide
- Common tasks tutorials
- Troubleshooting guide
- Best practices
- Video walkthroughs

## 10. Future Enhancements

### Version 2.0
- User attribute management
- Custom fields support
- Advanced audit reporting
- Role templates/groups
- Approval workflows

### Version 3.0
- Service-specific admin roles
- Delegated administration
- SSO provider integration
- Mobile app support
- Real-time notifications

## 11. Success Criteria

### Functional Success
- All user management operations work correctly
- Role assignment/revocation is reliable
- Search and filtering perform well
- Bulk operations complete successfully
- Audit trail is comprehensive

### Performance Success
- Page load time < 2 seconds
- API response time < 300ms average
- Support 1000+ concurrent users
- Handle 10,000+ users in database
- Search returns results in < 500ms

### Security Success
- No unauthorized access possible
- All operations are audited
- Sensitive data is protected
- OWASP top 10 compliance
- Passes security audit

### User Experience Success
- Intuitive interface
- Minimal training required
- Positive user feedback
- < 5% error rate
- Mobile responsive

## 12. Appendices

### Appendix A: Database Schema Changes

```sql
-- Audit log table
CREATE TABLE identity_audit_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id INTEGER,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for efficient querying
CREATE INDEX idx_audit_user_action ON identity_audit_log(user_id, action);
CREATE INDEX idx_audit_created ON identity_audit_log(created_at DESC);
```

### Appendix B: Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| AUTH_REQUIRED | Authentication required | 401 |
| PERMISSION_DENIED | Insufficient permissions | 403 |
| USER_NOT_FOUND | User does not exist | 404 |
| VALIDATION_ERROR | Input validation failed | 400 |
| DUPLICATE_USER | Username/email exists | 409 |
| ROLE_NOT_FOUND | Role does not exist | 404 |
| SERVICE_NOT_FOUND | Service not registered | 404 |
| EXPIRED_ASSIGNMENT | Role assignment expired | 400 |
| RATE_LIMITED | Too many requests | 429 |

### Appendix C: Configuration Examples

#### CIELO Website Integration
```python
# cielo_website/settings.py
INSTALLED_APPS = [
    # ... existing apps
    'vfadmin',
]

VFADMIN_CONFIG = {
    'IDENTITY_PROVIDER_URL': os.environ.get('IDENTITY_PROVIDER_URL'),
    'API_TIMEOUT': 30,
    'THEME': 'light',
    'SHOW_AUDIT_LOG': True,
    'ENABLE_BULK_OPERATIONS': True,
}

# Middleware to ensure admin access
MIDDLEWARE = [
    # ... existing middleware
    'vfadmin.middleware.AdminRequiredMiddleware',
]
```

#### Nginx Configuration
```nginx
location /admin/ {
    proxy_pass http://django_app;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";
}
```