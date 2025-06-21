# VFAdmin Specification - Implementation Decisions

## Decisions Made (2024-01-20)

### 1. Admin Role Model
- **Decision**: Create new `identity_admin` role
- **Implementation**: 
  - Add role to identity provider's initial data migration
  - Role name: `identity_admin`
  - Display name: "Identity Administrator"
  - Description: "Full access to user and role management"
  - Is global: True

### 2. UI Technology
- **Decision**: Server-side rendering with JavaScript for API interactions
- **Implementation**:
  - Django templates for page structure
  - Vanilla JavaScript for dynamic interactions
  - Fetch API for communicating with Identity Provider
  - No heavy frontend frameworks in v1

### 3. CSV Upload
- **Decision**: Defer to v2
- **v1 Scope**: JSON-based bulk operations only
- **v2 Feature**: CSV upload with template download

### 4. Audit Log Retention
- **Decision**: Out of scope for v1
- **Implementation**: 
  - Create audit logs for all operations
  - No automatic cleanup/retention policy
  - Can be addressed later based on requirements

### 5. Password Policy
- **Decision**: No specific policy for v1
- **Implementation**:
  - Use Django's default password validation
  - Minimum 8 characters (Django default)
  - Can't be entirely numeric
  - Can't be too common
  - Future enhancement for v2

### 6. Email Notifications
- **Decision**: No email notifications in v1
- **Implementation**:
  - No email sent on user creation
  - No email sent on role assignment
  - Password reset will be manual (admin sets password)
  - Can be added in future versions

## Updated Implementation Notes

### Identity Provider Changes

1. **Add identity_admin role to initial migration**:
```python
# identity_app/migrations/000X_add_identity_admin_role.py
def create_identity_admin_role(apps, schema_editor):
    Role = apps.get_model('identity_app', 'Role')
    Service = apps.get_model('identity_app', 'Service')
    
    # Get or create identity provider service
    service, _ = Service.objects.get_or_create(
        name='identity_provider',
        defaults={
            'display_name': 'Identity Provider',
            'description': 'Core identity and authentication service'
        }
    )
    
    # Create identity_admin role
    Role.objects.get_or_create(
        name='identity_admin',
        service=service,
        defaults={
            'display_name': 'Identity Administrator',
            'description': 'Full access to user and role management',
            'is_global': True
        }
    )
```

2. **Update permission check in API views**:
```python
from rest_framework.permissions import BasePermission

class IsIdentityAdmin(BasePermission):
    """Check if user has identity_admin role"""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        user_attrs = get_user_attributes(
            request.user.id, 
            'identity_provider'
        )
        return 'identity_admin' in getattr(user_attrs, 'roles', [])
```

### VFAdmin App Structure

```
vfadmin/
├── __init__.py
├── apps.py
├── urls.py
├── views.py
├── templates/
│   └── vfadmin/
│       ├── base.html
│       ├── users/
│       │   ├── list.html
│       │   ├── detail.html
│       │   └── create.html
│       └── includes/
│           ├── messages.html
│           └── pagination.html
├── static/
│   └── vfadmin/
│       ├── css/
│       │   └── vfadmin.css
│       └── js/
│           ├── api.js      # API client
│           ├── users.js    # User management
│           └── utils.js    # Utilities
└── templatetags/
    ├── __init__.py
    └── vfadmin_tags.py
```

### Simplified JavaScript API Client

```javascript
// vfadmin/static/vfadmin/js/api.js
class VFAdminAPI {
    constructor() {
        this.baseURL = window.VFADMIN_CONFIG.apiURL;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        try {
            const response = await fetch(url, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    ...options.headers
                },
                credentials: 'include'
            });

            const data = await response.json();

            if (!response.ok) {
                throw new APIError(data.error || 'Request failed', response.status);
            }

            return data;
        } catch (error) {
            this.handleError(error);
            throw error;
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    handleError(error) {
        console.error('API Error:', error);
        // Show user-friendly error message
        const messageEl = document.getElementById('message-container');
        if (messageEl) {
            messageEl.innerHTML = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    ${error.message || 'An error occurred'}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
        }
    }

    // User operations
    async getUsers(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/admin/users/?${queryString}`);
    }

    async getUser(id) {
        return this.request(`/api/admin/users/${id}/`);
    }

    async createUser(userData) {
        return this.request('/api/admin/users/', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
    }

    async updateUser(id, userData) {
        return this.request(`/api/admin/users/${id}/`, {
            method: 'PATCH',
            body: JSON.stringify(userData)
        });
    }

    async deleteUser(id) {
        return this.request(`/api/admin/users/${id}/`, {
            method: 'DELETE'
        });
    }

    // Role operations
    async getUserRoles(userId) {
        return this.request(`/api/admin/users/${userId}/roles/`);
    }

    async assignRole(userId, roleData) {
        return this.request(`/api/admin/users/${userId}/roles/`, {
            method: 'POST',
            body: JSON.stringify(roleData)
        });
    }

    async revokeRole(userId, roleId) {
        return this.request(`/api/admin/users/${userId}/roles/${roleId}/`, {
            method: 'DELETE'
        });
    }

    // Service operations
    async getServices() {
        return this.request('/api/admin/services/');
    }

    async getRoles(serviceName = null) {
        const params = serviceName ? { service: serviceName } : {};
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/admin/roles/?${queryString}`);
    }
}

// Global instance
window.vfadminAPI = new VFAdminAPI();
```

## Priority Order for Implementation

Based on the decisions, here's the recommended implementation order:

### Phase 1: Core API (Week 1)
1. Create `identity_admin` role
2. Implement user list/detail/create/update endpoints
3. Implement basic role assignment endpoints
4. Add permission checks

### Phase 2: Basic UI (Week 2)
1. Create VFAdmin Django app structure
2. Implement user list page with search
3. Implement user detail/edit page
4. Add user creation form

### Phase 3: Role Management (Week 3)
1. Add role assignment UI
2. Implement role revocation
3. Add service/role browser
4. Test cross-service scenarios

### Phase 4: Polish (Week 4)
1. Improve error handling
2. Add loading states
3. Implement pagination
4. Add comprehensive tests

This approach delivers a working system quickly while maintaining the flexibility to add advanced features later.