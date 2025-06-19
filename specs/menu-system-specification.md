# Menu System Specification

## Overview

This document specifies a distributed menu system for VF Services microservices architecture where individual services (billing, inventory, etc.) can publish menu items that consumer applications (like the website) can aggregate and display.

## System Architecture

```mermaid
graph TB
    subgraph Services
        INV[Inventory Service]
        BILL[Billing Service]
        IDP[Identity Provider]
    end
    
    subgraph Consumers
        WEB[Website - Django]
        REACT[React SPA]
        MOBILE[Mobile App]
    end
    
    subgraph Infrastructure
        REDIS[(Redis Cache)]
        GW[API Gateway]
    end
    
    INV -->|Menu API| GW
    BILL -->|Menu API| GW
    IDP -->|Permissions| GW
    
    GW <-->|Cache| REDIS
    
    GW -->|REST API| WEB
    GW -->|REST API| REACT
    GW -->|REST API| MOBILE
    
    style INV fill:#4A90E2
    style BILL fill:#4A90E2
    style IDP fill:#7B68EE
    style WEB fill:#50C878
    style REACT fill:#50C878
    style MOBILE fill:#50C878
    style GW fill:#FFD700
    style REDIS fill:#DC143C
```

## Industry Best Practices Analysis

### Common Approaches in Enterprise Applications

1. **Service Discovery Pattern** (Netflix, Spotify)
   - Services register their capabilities including UI elements
   - Central registry maintains menu contributions
   - Used in large-scale microservices

2. **API Gateway Aggregation** (Amazon, Uber)
   - Gateway aggregates menu items from multiple services
   - Single endpoint for consumers
   - Reduces client-side complexity

3. **Event-Driven Menu Updates** (Slack, Microsoft Teams)
   - Services publish menu changes to event bus
   - Consumers subscribe to menu updates
   - Real-time menu synchronization

4. **Static Configuration with Dynamic Permissions** (Google Workspace, Salesforce)
   - Menu structure defined centrally
   - Permissions checked at runtime
   - Easier to maintain consistent UX

## Recommended Approach for VF Services

Based on the current architecture and scale, we recommend a **Hybrid API-Based Approach with Caching**:

### Why This Approach?

1. **Fits existing architecture** - Aligns with current JWT-based auth and service communication
2. **Performance** - Redis caching prevents repeated API calls
3. **Flexibility** - Services maintain autonomy over their menus
4. **Simplicity** - No additional infrastructure required
5. **Industry-proven** - Similar to Shopify's app extension system

## Architecture Design

### 1. Menu Data Structure

```json
{
  "menu_name": "sidebar_menu",
  "items": [
    {
      "id": "inventory_main",
      "label": "Inventory",
      "url": "/inventory/",
      "icon": "box-icon",
      "order": 100,
      "permissions": ["inventory.view_product"],
      "app_name": "inventory",
      "children": [
        {
          "id": "inventory_products",
          "label": "Products",
          "url": "/inventory/products/",
          "permissions": ["inventory.view_product"]
        }
      ]
    }
  ]
}
```

### Menu Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant Website
    participant Gateway
    participant Cache
    participant Inventory
    participant Billing
    participant IDP

    User->>Website: Request Page
    Website->>Gateway: GET /api/gateway/menus/sidebar_menu/
    
    Gateway->>Cache: Check Cache
    alt Cache Hit
        Cache-->>Gateway: Return Cached Menu
    else Cache Miss
        Gateway->>IDP: Validate JWT Token
        IDP-->>Gateway: User Permissions
        
        par Parallel Requests
            Gateway->>Inventory: GET /api/menus/sidebar_menu/
            and
            Gateway->>Billing: GET /api/menus/sidebar_menu/
        end
        
        Inventory-->>Gateway: Menu Items (filtered)
        Billing-->>Gateway: Menu Items (filtered)
        
        Gateway->>Gateway: Aggregate & Sort
        Gateway->>Cache: Store Result
    end
    
    Gateway-->>Website: Aggregated Menu
    Website-->>User: Render Page with Menu
```

### 2. Service-Side Implementation

Each service implements:

#### Menu Manifest (`menu_manifest.py`)
```python
MENU_CONTRIBUTIONS = {
    'sidebar_menu': {
        'items': [
            {
                'id': 'inventory_main',
                'label': 'Inventory',
                'url': '/inventory/',
                'icon': 'box-icon',
                'order': 100,
                'permissions': ['inventory.view_product'],
                'children': [...]
            }
        ]
    },
    'top_menu': {
        'items': [...]
    }
}
```

#### Menu API Endpoint
```
GET /api/menus/{menu_name}/
Authorization: Bearer <JWT_TOKEN>

Response:
{
  "menu_name": "sidebar_menu",
  "items": [...],  // Filtered based on user permissions
  "app_name": "inventory",
  "version": "1.0"
}
```

### 3. Consumer-Side Implementation

#### Menu Service (`website/services/menu_service.py`)
```python
class MenuService:
    def __init__(self):
        self.cache = redis_client
        self.service_urls = {
            'inventory': settings.INVENTORY_API_URL,
            'billing': settings.BILLING_API_URL
        }
    
    def get_menu(self, menu_name, user_token):
        # Check cache first
        # Aggregate from multiple services
        # Filter based on permissions
        # Cache results
        return aggregated_menu
```

#### Template Tag Implementation
```python
@register.simple_tag(takes_context=True)
def get_menu(context, menu_name):
    request = context['request']
    menu_service = MenuService()
    return menu_service.get_menu(menu_name, request.user_token)
```

#### Template Usage
```django
{% load menu_tags %}
{% get_menu 'sidebar_menu' as sidebar %}

<nav class="sidebar">
  {% for item in sidebar.items %}
    <div class="menu-item">
      <a href="{{ item.url }}">
        <i class="{{ item.icon }}"></i>
        {{ item.label }}
      </a>
      {% if item.children %}
        <ul class="submenu">
          {% for child in item.children %}
            <li><a href="{{ child.url }}">{{ child.label }}</a></li>
          {% endfor %}
        </ul>
      {% endif %}
    </div>
  {% endfor %}
</nav>
```

### 4. React/SPA Consumer Implementation

The same API endpoints serve both Django templates and React applications, ensuring consistency across different frontend technologies.

#### Menu API Gateway Endpoint
```
GET /api/gateway/menus/{menu_name}/
Authorization: Bearer <JWT_TOKEN>

Response:
{
  "menu_name": "sidebar_menu",
  "items": [...],  // Aggregated from all services
  "metadata": {
    "version": "1.0",
    "cached_at": "2024-01-17T10:30:00Z",
    "ttl": 300
  }
}
```

#### React Hook Implementation
```javascript
// hooks/useMenu.js
import { useEffect, useState } from 'react';
import { useAuth } from './useAuth';

export const useMenu = (menuName) => {
  const [menu, setMenu] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    const fetchMenu = async () => {
      try {
        const response = await fetch(`/api/gateway/menus/${menuName}/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) throw new Error('Failed to fetch menu');
        
        const data = await response.json();
        setMenu(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      fetchMenu();
    }
  }, [menuName, token]);

  return { menu, loading, error };
};
```

#### React Component Implementation
```javascript
// components/Sidebar.jsx
import React from 'react';
import { useMenu } from '../hooks/useMenu';
import MenuItem from './MenuItem';

const Sidebar = () => {
  const { menu, loading, error } = useMenu('sidebar_menu');

  if (loading) return <div>Loading menu...</div>;
  if (error) return <div>Error loading menu</div>;
  if (!menu) return null;

  return (
    <nav className="sidebar">
      {menu.items.map(item => (
        <MenuItem key={item.id} item={item} />
      ))}
    </nav>
  );
};

// components/MenuItem.jsx
const MenuItem = ({ item }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="menu-item">
      <a href={item.url} onClick={(e) => {
        if (item.children?.length) {
          e.preventDefault();
          setExpanded(!expanded);
        }
      }}>
        <i className={item.icon}></i>
        {item.label}
      </a>
      {item.children && expanded && (
        <ul className="submenu">
          {item.children.map(child => (
            <MenuItem key={child.id} item={child} />
          ))}
        </ul>
      )}
    </div>
  );
};
```

#### State Management (Redux/Zustand)
```javascript
// store/menuSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

export const fetchMenu = createAsyncThunk(
  'menu/fetch',
  async ({ menuName, token }) => {
    const response = await fetch(`/api/gateway/menus/${menuName}/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
  }
);

const menuSlice = createSlice({
  name: 'menu',
  initialState: {
    menus: {},
    loading: false,
    error: null
  },
  reducers: {
    clearMenuCache: (state) => {
      state.menus = {};
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMenu.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchMenu.fulfilled, (state, action) => {
        state.loading = false;
        state.menus[action.meta.arg.menuName] = action.payload;
      })
      .addCase(fetchMenu.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message;
      });
  }
});
```

#### Next.js Server Components
```typescript
// app/components/ServerSidebar.tsx
import { headers } from 'next/headers';

async function getMenu(menuName: string) {
  const headersList = headers();
  const token = headersList.get('authorization');
  
  const response = await fetch(`${process.env.API_GATEWAY_URL}/menus/${menuName}/`, {
    headers: { 'Authorization': token },
    next: { revalidate: 300 } // 5 minute cache
  });
  
  if (!response.ok) return null;
  return response.json();
}

export default async function ServerSidebar() {
  const menu = await getMenu('sidebar_menu');
  
  if (!menu) return null;
  
  return (
    <nav className="sidebar">
      {menu.items.map((item) => (
        <MenuItemServer key={item.id} item={item} />
      ))}
    </nav>
  );
}
```

### 5. API Gateway for Frontend Applications

To better serve React/SPA applications, implement an API gateway pattern:

```python
# website/api/views.py
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

@method_decorator(cache_page(60 * 5), name='dispatch')  # 5 min cache
class MenuGatewayView(APIView):
    def get(self, request, menu_name):
        menu_service = MenuService()
        
        # Get user token from request
        token = request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
        
        # Aggregate menus from all services
        aggregated_menu = menu_service.get_aggregated_menu(menu_name, token)
        
        # Add CORS headers for SPA
        response = JsonResponse(aggregated_menu)
        response['Access-Control-Allow-Origin'] = settings.ALLOWED_ORIGINS
        response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
        
        return response
```

### 6. WebSocket Support for Real-time Updates

For dynamic menu updates without page refresh:

```javascript
// React WebSocket implementation
const useMenuWebSocket = (menuName) => {
  const [menu, setMenu] = useState(null);
  const { token } = useAuth();

  useEffect(() => {
    const ws = new WebSocket(`wss://api.example.com/ws/menus/`);
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'subscribe',
        menu: menuName,
        token: token
      }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'menu_update' && data.menu_name === menuName) {
        setMenu(data.menu);
      }
    };
    
    return () => ws.close();
  }, [menuName, token]);
  
  return menu;
};
```

### 7. Migration Strategy: Django to React

```mermaid
graph LR
    subgraph Phase 1: Dual Support
        DT1[Django Templates]
        RT1[React Components]
        MS1[Menu Service]
        API1[Menu API]
        
        DT1 --> MS1
        RT1 --> API1
        MS1 --> API1
    end
    
    subgraph Phase 2: Gradual Migration
        DT2[Legacy Django Pages]
        RT2[New React Features]
        API2[Shared Menu API]
        
        DT2 --> API2
        RT2 --> API2
    end
    
    subgraph Phase 3: Full SPA
        RT3[React/Next.js Frontend]
        API3[API-Only Backend]
        
        RT3 --> API3
    end
    
    Phase1 --> Phase2
    Phase2 --> Phase3
    
    style DT1 fill:#FFB6C1
    style DT2 fill:#FFB6C1
    style RT1 fill:#90EE90
    style RT2 fill:#90EE90
    style RT3 fill:#90EE90
```

### 8. Performance Optimizations for SPAs

1. **Bundle Optimization**
   ```javascript
   // Lazy load menu components
   const Sidebar = lazy(() => import('./components/Sidebar'));
   ```

2. **Service Worker Caching**
   ```javascript
   // Cache menu responses
   self.addEventListener('fetch', (event) => {
     if (event.request.url.includes('/api/gateway/menus/')) {
       event.respondWith(
         caches.match(event.request).then(response => {
           return response || fetch(event.request);
         })
       );
     }
   });
   ```

3. **GraphQL Alternative**
   ```graphql
   query GetMenu($menuName: String!, $locale: String) {
     menu(name: $menuName, locale: $locale) {
       items {
         id
         label
         url
         icon
         permissions
         children {
           id
           label
           url
         }
       }
     }
   }
   ```

## Implementation Phases

```mermaid
gantt
    title Menu System Implementation Roadmap
    dateFormat YYYY-MM-DD
    section Phase 1 MVP
    Menu Manifest Design    :done, p1-1, 2024-01-15, 2d
    Inventory API Endpoint  :active, p1-2, after p1-1, 3d
    Website Template Tag    :p1-3, after p1-2, 2d
    Permission Filtering    :p1-4, after p1-2, 2d
    Integration Testing     :p1-5, after p1-3, 2d
    
    section Phase 2 Performance
    Redis Cache Layer       :p2-1, after p1-5, 3d
    Cache Invalidation      :p2-2, after p2-1, 2d
    Menu Versioning         :p2-3, after p2-1, 2d
    Load Testing            :p2-4, after p2-3, 1d
    
    section Phase 3 Advanced
    WebSocket Support       :p3-1, after p2-4, 4d
    Menu Personalization    :p3-2, after p3-1, 3d
    A/B Testing             :p3-3, after p3-2, 3d
    Analytics Integration   :p3-4, after p3-2, 2d
```

### Phase 1: Basic Implementation (MVP)
1. Create menu manifest in inventory service
2. Implement menu API endpoint
3. Create template tag in website
4. Basic permission filtering

### Phase 2: Performance Optimization
1. Add Redis caching
2. Implement cache invalidation
3. Add menu versioning

### Phase 3: Advanced Features
1. Dynamic menu updates via WebSocket
2. Menu personalization
3. A/B testing support
4. Analytics integration

## Security Considerations

```mermaid
flowchart TD
    A[Menu Request] --> B{JWT Valid?}
    B -->|No| C[401 Unauthorized]
    B -->|Yes| D[Extract Permissions]
    
    D --> E[Request Service Menus]
    E --> F{Service Available?}
    F -->|No| G[Skip Service]
    F -->|Yes| H[Filter by Permissions]
    
    H --> I{User Has Permission?}
    I -->|No| J[Exclude Menu Item]
    I -->|Yes| K[Include Menu Item]
    
    K --> L[Aggregate Results]
    J --> L
    G --> L
    
    L --> M{Cache Enabled?}
    M -->|Yes| N[Store in Cache with User Key]
    M -->|No| O[Return Response]
    N --> O
    
    style C fill:#FF6B6B
    style J fill:#FFE66D
    style K fill:#4ECDC4
```

1. **Permission Validation**
   - Always validate permissions server-side
   - Never trust client-side permission checks
   - Use JWT claims for permission verification

2. **URL Security**
   - Validate all URLs to prevent injection
   - Use relative URLs where possible
   - Sanitize user-provided content

3. **Cache Security**
   - Include user ID in cache keys
   - Set appropriate TTL values
   - Clear cache on permission changes

## Performance Considerations

1. **Caching Strategy**
   - Cache menus per user (includes permissions)
   - TTL: 5 minutes (configurable)
   - Invalidate on user permission changes

2. **API Optimization**
   - Parallel API calls to services
   - Timeout handling (2 seconds per service)
   - Graceful degradation if service unavailable

3. **Frontend Optimization**
   - Lazy load submenus
   - Progressive enhancement
   - Local storage for static menu structure

## Configuration

### Environment Variables
```bash
# Website settings
MENU_CACHE_TTL=300  # 5 minutes
MENU_API_TIMEOUT=2  # seconds
MENU_AGGREGATION_ENABLED=true

# Service URLs
INVENTORY_API_URL=http://inventory-api:8000
BILLING_API_URL=http://billing-api:8000
```

### Django Settings
```python
MENU_CONFIG = {
    'CACHE_TTL': int(os.getenv('MENU_CACHE_TTL', 300)),
    'API_TIMEOUT': int(os.getenv('MENU_API_TIMEOUT', 2)),
    'AGGREGATION_ENABLED': os.getenv('MENU_AGGREGATION_ENABLED', 'true') == 'true',
    'SERVICE_URLS': {
        'inventory': os.getenv('INVENTORY_API_URL'),
        'billing': os.getenv('BILLING_API_URL'),
    }
}
```

## Testing Strategy

1. **Unit Tests**
   - Menu manifest validation
   - Permission filtering logic
   - Cache operations

2. **Integration Tests**
   - Service-to-service menu fetching
   - Aggregation logic
   - Error handling

3. **E2E Tests**
   - Menu rendering in browser
   - Permission-based visibility
   - Performance benchmarks

## Monitoring and Observability

### Monitoring Architecture

```mermaid
graph TB
    subgraph Services
        S1[Service APIs]
        S2[Gateway API]
        S3[Cache Layer]
    end
    
    subgraph Metrics Collection
        M1[Response Times]
        M2[Cache Hit Rate]
        M3[Error Rate]
        M4[Permission Denials]
    end
    
    subgraph Monitoring Stack
        PROM[Prometheus]
        GRAF[Grafana]
        ELK[ELK Stack]
        ALERT[AlertManager]
    end
    
    S1 --> M1
    S2 --> M1
    S3 --> M2
    S1 --> M3
    S2 --> M3
    S2 --> M4
    
    M1 --> PROM
    M2 --> PROM
    M3 --> PROM
    M4 --> PROM
    
    PROM --> GRAF
    PROM --> ALERT
    S1 --> ELK
    S2 --> ELK
    S3 --> ELK
    
    style PROM fill:#FF6B35
    style GRAF fill:#F37626
    style ELK fill:#FFC61E
    style ALERT fill:#E43D30
```

1. **Metrics to Track**
   - Menu API response times
   - Cache hit/miss rates
   - Aggregation failures
   - Menu render times

2. **Logging**
   - API requests/responses
   - Permission denials
   - Cache operations
   - Error conditions

## Migration Plan

1. **Rollout Strategy**
   - Start with inventory service
   - Test with subset of users
   - Gradually add more services
   - Full production rollout

2. **Rollback Plan**
   - Feature flag for menu system
   - Fallback to static menus
   - Cache clear procedure

## Future Enhancements

### Menu Builder UI Concept

```mermaid
graph TD
    subgraph Admin Interface
        UI[Menu Builder UI]
        PREVIEW[Preview Panel]
        PERM[Permission Manager]
    end
    
    subgraph Storage
        DB[(Menu Database)]
        VERS[Version Control]
    end
    
    subgraph Distribution
        API[Menu API]
        WEBHOOK[Webhook Notifier]
        CACHE[Cache Invalidator]
    end
    
    UI -->|Drag & Drop| DB
    UI --> PREVIEW
    UI --> PERM
    
    DB --> VERS
    DB --> API
    
    API --> WEBHOOK
    API --> CACHE
    
    WEBHOOK -->|Notify| S1[Service 1]
    WEBHOOK -->|Notify| S2[Service 2]
    WEBHOOK -->|Notify| S3[Service N]
    
    style UI fill:#4CAF50
    style PREVIEW fill:#2196F3
    style PERM fill:#FF9800
```

1. **Menu Builder UI**
   - Admin interface for menu management
   - Drag-and-drop menu organization
   - Preview functionality

2. **Advanced Permissions**
   - Feature flags integration
   - Role-based menu variations
   - Time-based menu items

3. **Analytics Integration**
   - Click tracking
   - User journey analysis
   - Menu optimization insights

## Conclusion

This menu system provides a scalable, maintainable solution for distributed menu management in a microservices architecture. The hybrid approach balances performance, flexibility, and simplicity while following industry best practices.