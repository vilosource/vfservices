# Menu System Implementation - Material Design

## Overview

The VF Services menu system is a distributed menu management solution with Material Design UI that allows individual microservices to declare menu items that can be aggregated and displayed by consumer applications.

## Key Components

### 1. Menu Manifest (Service Side)

Each service declares its menu contributions in a `menu_manifest.py` file:

```python
# inventory-api/inventory/menu_manifest.py
MENU_CONTRIBUTIONS = {
    'sidebar_menu': {
        'items': [
            {
                'id': 'inventory_main',
                'label': 'Inventory',
                'url': '/inventory/',
                'icon': 'box',  # MDI icon (only for top-level)
                'order': 100,
                'permissions': ['inventory.view_product'],
                'children': [
                    {
                        'id': 'inventory_products',
                        'label': 'Products',  # No icon for submenus
                        'url': '/inventory/products/',
                        'permissions': ['inventory.view_product'],
                        'children': [...]
                    }
                ]
            }
        ]
    }
}
```

### 2. Menu API Endpoint (Service Side)

Each service exposes a menu API endpoint that filters menu items based on user permissions:

```python
# GET /api/menus/{menu_name}/
# Returns menu items filtered by user permissions
```

### 3. Menu Service (Consumer Side)

The website aggregates menus from multiple services:

```python
# website/webapp/services/menu_service.py
class MenuService:
    def get_menu(self, menu_name, user_token):
        # Fetches from all services in parallel
        # Aggregates and caches results
        # Returns sorted menu items
```

### 4. Template Tags (Consumer Side)

Django template tags make it easy to render menus:

```django
{% load menu_tags %}
{% render_sidebar_menu %}
```

### 5. Material Design Templates

The menu uses Bootstrap 5 collapse components with Material Design styling:

```html
<!-- sidebar_menu.html -->
<div id="sidebar-menu">
    <ul id="side-menu">
        <li class="menu-title">Navigation</li>
        {% render_menu_item item %}
    </ul>
</div>

<!-- menu_item.html -->
<li>
    <a href="#{{ item.id }}" 
       data-bs-toggle="collapse" 
       class="waves-effect">
        <i class="mdi mdi-{{ item.icon }}"></i>
        <span>{{ item.label }}</span>
    </a>
    <div class="collapse" id="{{ item.id }}">
        <ul class="nav-second-level">
            <!-- Nested items -->
        </ul>
    </div>
</li>
```

## Architecture Flow

1. **User visits dashboard** → JWT token in cookie
2. **Template tag invoked** → Extracts JWT token
3. **Menu service called** → Checks Redis cache
4. **If cache miss** → Parallel API calls to services
5. **Services filter menus** → Based on user permissions
6. **Results aggregated** → Sorted and cached
7. **Menu rendered** → Material Design HTML with Bootstrap 5

## Key Features

### Material Design UI
- Clean, modern interface matching material theme
- Material Design Icons (MDI) for top-level items only
- Bootstrap 5 collapse for smooth animations
- Wave ripple effects on click
- Consistent color scheme (#3d7eff for active/hover)

### Permission-Based Filtering
- Services only return menu items the user has permission to see
- Uses RBAC roles mapped to permissions
- No client-side permission checks needed

### Performance Optimizations
- Redis caching (5-minute TTL)
- Parallel API calls to services
- Service timeout handling (2 seconds)
- Graceful degradation if service unavailable
- LocalStorage for menu state persistence

### Security
- Server-side permission validation
- JWT token authentication
- No sensitive data in menu responses
- Cache keys include user identifier

## Testing

Run the test script to verify the menu system:

```bash
python test_menu_simple.py
```

Expected output:
- ✓ Successful login
- ✓ Menu API returns items based on user role
- ✓ Dashboard displays menu component

## Configuration

### Service Side
```python
# inventory-api/inventory/urls.py
path('menus/<str:menu_name>/', views.get_menu, name='get_menu'),
```

### Consumer Side
```python
# website/main/settings.py
MENU_CACHE_TTL = 300  # 5 minutes
MENU_API_TIMEOUT = 2  # 2 seconds
INVENTORY_API_URL = "http://inventory-api:8000"
BILLING_API_URL = "http://billing-api:8000"
```

## Future Enhancements

1. **Menu Builder UI** - Admin interface for visual menu management
2. **WebSocket Updates** - Real-time menu updates
3. **GraphQL Support** - Alternative to REST API
4. **React Components** - For SPA applications
5. **Menu Analytics** - Track menu usage patterns

## Implementation Status

- ✅ Menu manifest system
- ✅ Service API endpoints  
- ✅ Menu aggregation service
- ✅ Template tags with Material Design
- ✅ Permission filtering
- ✅ Redis caching
- ✅ Bootstrap 5 collapse integration
- ✅ Material Design Icons (MDI)
- ✅ Wave ripple effects
- ✅ Menu state persistence
- ✅ Responsive design
- ✅ Basic testing

The menu system with Material Design is fully functional and ready for production use.