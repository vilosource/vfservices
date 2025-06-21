# Identity Admin Django App Specification

## Overview

The `identity-admin` is a reusable Django application that provides a comprehensive user interface for managing users, roles, and attributes in the VFServices Identity Provider system. This app can be integrated into any Django project within the VFServices ecosystem to provide identity administration capabilities.

## Goals

1. **Reusability**: Create a Django app that can be easily integrated into any VFServices Django project
2. **Consistency**: Provide a consistent UI/UX using the Material Theme design system
3. **Security**: Enforce proper RBAC-ABAC permissions for all administrative actions
4. **Real-time Data**: Always fetch fresh data from Identity Provider API (no caching)
5. **User Experience**: Create an intuitive interface for complex identity management tasks

## Phase 1 Scope

This specification focuses on Phase 1 implementation with the following features:
- User management (create, edit, deactivate, search)
- Role assignment/revocation with role profiles
- Service/role browsing
- User attribute management
- Replace Django admin (/admin) with identity-admin interface

Features deferred to Phase 2:
- Audit trail display
- Bulk operations
- Export functionality
- Notification system
- Advanced search filters

## Architecture

### High-Level Architecture

```
Django Project (e.g., website, cielo-website)
    │
    ├── common/apps/identity-admin/  ← Reusable Django App
    │   ├── Views (Server-side rendering)
    │   ├── API Client (Python)
    │   ├── Templates (Material Theme)
    │   └── Static Assets (JS/CSS)
    │
    └── Identity Provider API  ← External Service
        └── Admin endpoints (/api/admin/*)
```

### Integration Flow

1. User accesses identity admin interface through host Django project
2. Django views use JWT token from current session
3. Views make server-side API calls to Identity Provider
4. JavaScript provides dynamic updates for better UX
5. All actions are audited in Identity Provider

## Technical Specifications

### 1. Django App Structure

```
common/apps/identity-admin/
├── __init__.py
├── apps.py                      # Django app configuration
├── urls.py                      # URL patterns
├── views.py                     # Main view classes
├── api_client.py                # Identity Provider API client
├── forms.py                     # Django forms for validation
├── decorators.py                # Permission decorators
├── exceptions.py                # Custom exception classes
├── utils.py                     # Helper functions
├── templates/
│   └── identity_admin/
│       ├── base.html           # Base template with navigation
│       ├── includes/           # Reusable template components
│       │   ├── user_table.html
│       │   ├── role_selector.html
│       │   └── attribute_editor.html
│       ├── users/
│       │   ├── list.html      # User list with DataTable
│       │   ├── detail.html    # User detail/edit
│       │   ├── create.html    # Create new user
│       │   └── bulk_assign.html # Bulk role assignment
│       ├── roles/
│       │   ├── list.html      # Role browser
│       │   └── assign.html    # Role assignment interface
│       ├── services/
│       │   └── list.html      # Service registry
│       └── audit/
│           └── log.html        # Audit log viewer
├── static/
│   └── identity_admin/
│       ├── css/
│       │   └── identity-admin.css  # Custom styles
│       └── js/
│           ├── api-client.js       # JavaScript API client
│           ├── users.js            # User management JS
│           ├── roles.js            # Role management JS
│           └── datatables-init.js # DataTable configuration
├── templatetags/
│   ├── __init__.py
│   └── identity_admin_tags.py  # Custom template tags
└── tests/
    ├── test_views.py
    ├── test_api_client.py
    └── test_decorators.py
```

### 2. URL Configuration

```python
# urls.py
app_name = 'identity_admin'

urlpatterns = [
    # Main dashboard (replaces /admin)
    path('', DashboardView.as_view(), name='dashboard'),
    
    # User Management
    path('users/', UserListView.as_view(), name='user_list'),
    path('users/create/', UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/edit/', UserEditView.as_view(), name='user_edit'),
    path('users/<int:user_id>/roles/', UserRolesView.as_view(), name='user_roles'),
    
    # Role Management
    path('roles/', RoleListView.as_view(), name='role_list'),
    path('roles/assign/', RoleAssignView.as_view(), name='role_assign'),
    
    # Service Registry
    path('services/', ServiceListView.as_view(), name='service_list'),
    
    # API Endpoints (for AJAX)
    path('api/users/<int:user_id>/roles/', UserRolesAPIView.as_view(), name='api_user_roles'),
    path('api/users/<int:user_id>/attributes/', UserAttributesAPIView.as_view(), name='api_user_attributes'),
]
```

### Integration with Host Project

To replace Django admin with identity-admin:

```python
# In host project's urls.py
from django.urls import path, include

urlpatterns = [
    # Replace default admin with identity-admin
    path('admin/', include('identity_admin.urls')),
    # Remove or comment out: path('admin/', admin.site.urls),
    
    # Other URLs...
]
```

### 3. View Specifications

#### Base View Class

```python
class IdentityAdminBaseView(View):
    """Base view with common functionality"""
    
    def dispatch(self, request, *args, **kwargs):
        # Check for identity_admin role
        if not self.has_admin_permission(request):
            return HttpResponseForbidden()
        
        # Initialize API client with JWT token
        self.api_client = self.get_api_client(request)
        
        return super().dispatch(request, *args, **kwargs)
```

#### User List View

**Features:**
- Server-side pagination (50 users per page)
- Search by username, email, name
- Filter by: active status, role, service
- Sort by: username, email, date joined, last login
- Bulk actions: activate/deactivate

**Implementation:**
- Use DataTables for client-side table features
- Server-side filtering through API parameters
- Responsive design for mobile devices

#### User Detail View

**Features:**
- Display user information
- Role management interface
- Attribute editor
- Activity timeline
- Quick actions: reset password, deactivate

**Sections:**
1. **Basic Information**: Username, email, name, status
2. **Roles**: Current roles with expiration, grouped by service
3. **Attributes**: Editable attributes with proper input types
4. **Activity**: Recent role changes and logins

#### Role Assignment Interface

**Features:**
- User search with autocomplete
- Service and role selection
- Expiration date picker
- Assignment reason field
- **Role Profiles** for quick assignment

**Role Profiles:**

```python
ROLE_PROFILES = {
    'super_admin': {
        'name': 'Super Administrator',
        'description': 'Full system access',
        'roles': [
            ('identity_admin', 'identity_provider'),
            ('billing_admin', 'billing_api'),
            ('inventory_admin', 'inventory_api'),
            ('costs_admin', 'azure_costs'),
            ('cielo_admin', 'cielo_website'),
        ]
    },
    'operations_manager': {
        'name': 'Operations Manager',
        'description': 'Manages inventory and warehouse operations',
        'roles': [
            ('inventory_manager', 'inventory_api'),
            ('warehouse_manager', 'inventory_api'),
            ('movement_manager', 'inventory_api'),
        ]
    },
    'finance_manager': {
        'name': 'Finance Manager',
        'description': 'Manages billing and costs',
        'roles': [
            ('billing_admin', 'billing_api'),
            ('costs_manager', 'azure_costs'),
            ('payment_manager', 'billing_api'),
        ]
    },
    'customer_service': {
        'name': 'Customer Service Representative',
        'description': 'Handles customer accounts and subscriptions',
        'roles': [
            ('customer_manager', 'identity_provider'),
            ('invoice_manager', 'billing_api'),
            ('subscription_manager', 'billing_api'),
        ]
    },
    'cost_analyst': {
        'name': 'Cost Analyst',
        'description': 'Analyzes costs and cloud usage',
        'roles': [
            ('costs_viewer', 'azure_costs'),
            ('cost_analyst', 'cielo_website'),
            ('cielo_viewer', 'cielo_website'),
        ]
    },
    'warehouse_supervisor': {
        'name': 'Warehouse Supervisor',
        'description': 'Supervises warehouse operations',
        'roles': [
            ('warehouse_manager', 'inventory_api'),
            ('stock_manager', 'inventory_api'),
            ('count_supervisor', 'inventory_api'),
        ]
    },
    'auditor': {
        'name': 'Auditor',
        'description': 'Read-only access for audit purposes',
        'roles': [
            ('identity_viewer', 'identity_provider'),
            ('invoice_viewer', 'billing_api'),
            ('payment_viewer', 'billing_api'),
            ('costs_viewer', 'azure_costs'),
            ('movement_viewer', 'inventory_api'),
        ]
    }
}
```

### 4. API Client Specification (Phase 1)

```python
class IdentityAdminAPIClient:
    """Client for Identity Provider Admin API - No caching per requirements"""
    
    def __init__(self, jwt_token: str, base_url: str, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {jwt_token}',
            'Content-Type': 'application/json'
        })
        self.base_url = base_url
        self.timeout = timeout
    
    # User Management Methods
    def list_users(self, page=1, page_size=50, search=None, **filters):
        """List users with pagination and filtering - always fetches fresh data"""
        
    def get_user(self, user_id):
        """Get user details including roles - always fetches fresh data"""
        
    def create_user(self, user_data):
        """Create new user with optional initial roles"""
        
    def update_user(self, user_id, user_data):
        """Update user information"""
        
    def deactivate_user(self, user_id):
        """Soft delete user"""
        
    # Role Management Methods
    def list_user_roles(self, user_id):
        """Get user's current roles - always fetches fresh data"""
        
    def assign_role(self, user_id, role_name, service_name, expires_at=None, reason=None):
        """Assign role to user"""
        
    def revoke_role(self, user_id, role_id, reason=None):
        """Revoke role from user"""
        
    def assign_role_profile(self, user_id, profile_key, expires_at=None, reason=None):
        """Assign a role profile (set of roles) to user"""
        profile = ROLE_PROFILES.get(profile_key)
        if not profile:
            raise ValueError(f"Unknown role profile: {profile_key}")
        
        results = []
        for role_name, service_name in profile['roles']:
            try:
                result = self.assign_role(user_id, role_name, service_name, expires_at, reason)
                results.append({'success': True, 'role': role_name, 'service': service_name})
            except Exception as e:
                results.append({'success': False, 'role': role_name, 'service': service_name, 'error': str(e)})
        
        return results
        
    # Service and Role Methods
    def list_services(self):
        """List all registered services - always fetches fresh data"""
        
    def list_roles(self, service=None, is_global=None):
        """List all available roles - always fetches fresh data"""
```

### 5. JavaScript Components

#### API Client (api-client.js)

```javascript
class IdentityAdminClient {
    constructor() {
        this.baseUrl = window.IDENTITY_PROVIDER_URL || '';
        this.token = this.getJWTToken();
    }
    
    getJWTToken() {
        // Extract from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'jwt_token') {
                return value;
            }
        }
        return null;
    }
    
    async request(url, options = {}) {
        const response = await fetch(this.baseUrl + url, {
            ...options,
            headers: {
                'Authorization': `Bearer ${this.token}`,
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return response.json();
    }
    
    // API methods matching Python client
}
```

#### User Management (users.js)

```javascript
class UserManager {
    constructor() {
        this.apiClient = new IdentityAdminClient();
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Role assignment
        document.querySelectorAll('.assign-role-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleRoleAssign(e));
        });
        
        // Attribute editing
        document.querySelectorAll('.edit-attribute').forEach(input => {
            input.addEventListener('change', (e) => this.handleAttributeUpdate(e));
        });
    }
    
    async handleRoleAssign(event) {
        // Show role assignment modal
        // Handle form submission
        // Update UI on success
    }
    
    async handleAttributeUpdate(event) {
        // Validate input based on type
        // Send update to API
        // Show success/error feedback
    }
}
```

### 6. Template Specifications

#### Base Template Structure

```django
{# base.html #}
{% load static %}
<!DOCTYPE html>
<html lang="en" data-topbar-color="brand">
<head>
    <meta charset="utf-8" />
    <title>{% block title %}Identity Admin{% endblock %} | {{ site_name }}</title>
    
    {# Material Theme CSS #}
    <link href="{% static 'css/bootstrap.min.css' %}" rel="stylesheet" type="text/css" />
    <link href="{% static 'css/app.min.css' %}" rel="stylesheet" type="text/css" />
    <link href="{% static 'css/icons.min.css' %}" rel="stylesheet" type="text/css" />
    
    {# DataTables CSS #}
    {% block extra_css %}{% endblock %}
    
    {# Identity Admin CSS #}
    <link href="{% static 'identity_admin/css/identity-admin.css' %}" rel="stylesheet" type="text/css" />
</head>
<body>
    <div id="wrapper">
        {% include 'includes/topbar.html' %}
        {% include 'includes/sidebar.html' %}
        
        <div class="content-page">
            <div class="content">
                <div class="container-fluid">
                    {% block breadcrumb %}{% endblock %}
                    {% block content %}{% endblock %}
                </div>
            </div>
        </div>
    </div>
    
    {# JavaScript #}
    <script src="{% static 'js/vendor.min.js' %}"></script>
    <script src="{% static 'js/app.min.js' %}"></script>
    
    <script>
        window.IDENTITY_PROVIDER_URL = '{{ identity_provider_url }}';
    </script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>
```

#### User List Template

```django
{# users/list.html #}
{% extends 'identity_admin/base.html' %}
{% load identity_admin_tags %}

{% block content %}
<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-body">
                <div class="row mb-2">
                    <div class="col-sm-4">
                        <a href="{% url 'identity_admin:user_create' %}" class="btn btn-danger mb-2">
                            <i class="mdi mdi-plus-circle me-1"></i> Add User
                        </a>
                    </div>
                    <div class="col-sm-8">
                        <div class="text-sm-end">
                            <button type="button" class="btn btn-light mb-2">Export</button>
                            <button type="button" class="btn btn-light mb-2" id="bulk-assign-btn">
                                Bulk Assign Roles
                            </button>
                        </div>
                    </div>
                </div>

                <table id="users-datatable" class="table table-striped dt-responsive nowrap w-100">
                    <thead>
                        <tr>
                            <th>Username</th>
                            <th>Email</th>
                            <th>Name</th>
                            <th>Status</th>
                            <th>Roles</th>
                            <th>Last Login</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for user in users %}
                        <tr>
                            <td>{{ user.username }}</td>
                            <td>{{ user.email }}</td>
                            <td>{{ user.first_name }} {{ user.last_name }}</td>
                            <td>
                                {% if user.is_active %}
                                    <span class="badge bg-success">Active</span>
                                {% else %}
                                    <span class="badge bg-danger">Inactive</span>
                                {% endif %}
                            </td>
                            <td>
                                {% for role in user.roles|slice:":3" %}
                                    <span class="badge bg-primary">{{ role }}</span>
                                {% endfor %}
                                {% if user.roles|length > 3 %}
                                    <span class="badge bg-secondary">+{{ user.roles|length|add:"-3" }}</span>
                                {% endif %}
                            </td>
                            <td>{{ user.last_login|date:"Y-m-d H:i" }}</td>
                            <td>
                                <a href="{% url 'identity_admin:user_detail' user.id %}" 
                                   class="action-icon" title="View">
                                    <i class="mdi mdi-eye"></i>
                                </a>
                                <a href="{% url 'identity_admin:user_edit' user.id %}" 
                                   class="action-icon" title="Edit">
                                    <i class="mdi mdi-pencil"></i>
                                </a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 7. Permission Model

The app enforces the following permission model:

1. **Access Control**: All views require `identity_admin` role
2. **JWT Authentication**: Uses existing JWT token from session
3. **API Authorization**: All API calls include Bearer token
4. **Audit Trail**: All actions are logged in Identity Provider

### 8. Error Handling

#### API Error Responses

```python
class APIError(Exception):
    """Base exception for API errors"""
    pass

class AuthenticationError(APIError):
    """JWT token invalid or expired"""
    pass

class PermissionError(APIError):
    """User lacks required permissions"""
    pass

class ValidationError(APIError):
    """Invalid data provided"""
    pass
```

#### User-Friendly Error Display

- API errors shown as Bootstrap alerts
- Form validation errors displayed inline
- Network errors trigger retry mechanisms
- 404 errors show custom "User not found" page

### 9. Performance Considerations (Updated for Phase 1)

1. **No Caching**: Always fetch fresh data from Identity Provider API
2. **Pagination**: Server-side pagination for user lists (50 per page)
3. **Lazy Loading**: Load user details only when needed
4. **Debouncing**: Debounce search inputs (300ms delay)
5. **Loading States**: Show spinners during API calls

### 10. Security Requirements

1. **CSRF Protection**: Use Django's CSRF tokens for forms
2. **XSS Prevention**: Escape all user-generated content
3. **Authorization**: Verify permissions on both client and server
4. **Audit Logging**: Log all administrative actions
5. **Input Validation**: Validate all inputs on both client and server

### 11. Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari, Chrome Mobile

### 12. Accessibility

- WCAG 2.1 Level AA compliance
- Keyboard navigation support
- Screen reader compatible
- Proper ARIA labels
- High contrast mode support

### 13. Internationalization

- Not required for Phase 1
- Prepare structure for future i18n support

### 14. Testing Requirements

#### Unit Tests
- Test all view classes
- Test API client methods
- Test permission decorators
- Test form validation

#### Integration Tests
- Test full user creation flow
- Test role assignment workflow
- Test error handling scenarios

#### JavaScript Tests
- Test API client
- Test form validation
- Test dynamic UI updates

### 15. Documentation Requirements

1. **Developer Documentation**
   - Installation guide
   - Configuration options
   - API client usage examples
   - Template customization guide

2. **User Documentation**
   - User management guide
   - Role assignment procedures
   - Troubleshooting common issues

### 16. Configuration

The app should be configurable through Django settings:

```python
IDENTITY_ADMIN = {
    'API_TIMEOUT': 30,  # seconds
    'PAGE_SIZE': 50,    # users per page
    'IDENTITY_PROVIDER_URL': os.environ.get('IDENTITY_PROVIDER_URL', 'https://identity.vfservices.viloforge.com'),
    'ROLE_PROFILES': ROLE_PROFILES,  # Can be customized per deployment
    'CUSTOM_CSS': None,  # Path to custom CSS file
    'CUSTOM_JS': None,   # Path to custom JS file
}
```

### 17. Future Enhancements

1. **Phase 2**
   - Audit trail display
   - Bulk operations (bulk assign/revoke roles)
   - Export functionality (CSV/Excel)
   - Notification system for role changes
   - Advanced search filters
   - Navigation integration (auto-show for identity_admin users)
   - Multi-language support

2. **Phase 3**
   - Policy editor for ABAC rules
   - Visual role hierarchy
   - Compliance reporting
   - Multi-factor authentication management
   - API rate limiting dashboard
   - Role analytics and usage reports

## Phase 1 Implementation Timeline

1. **Week 1**: Core infrastructure
   - Django app structure
   - API client implementation
   - Base templates with Material Theme
   - Permission decorators

2. **Week 2**: User Management
   - User list view with DataTables
   - User detail/edit views
   - Create user functionality
   - User search

3. **Week 3**: Role Management
   - Role assignment interface
   - Role profiles implementation
   - Service/role browser
   - Role revocation

4. **Week 4**: Integration & Polish
   - Attribute management
   - JavaScript enhancements
   - Error handling
   - Testing and documentation

## Success Metrics

1. **Performance**: Page load time < 2 seconds
2. **Reliability**: 99.9% uptime for admin operations
3. **Usability**: Task completion rate > 95%
4. **Security**: Zero security incidents
5. **Adoption**: Used by all VFServices projects within 3 months