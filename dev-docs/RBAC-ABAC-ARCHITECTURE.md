# RBAC-ABAC System Architecture

## Executive Summary

The VF Services RBAC-ABAC system implements a hybrid authorization model combining Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC). This architecture enables fine-grained permissions across microservices while maintaining service autonomy and high performance through Redis caching.

## Design Principles

### 1. Service Autonomy
Each microservice declares and manages its own authorization requirements through service manifests, avoiding tight coupling with the identity provider.

### 2. Performance First
Redis caching layer ensures authorization checks don't impact API response times, with sub-millisecond attribute lookups.

### 3. Developer Experience
Simple decorators and mixins make implementing complex authorization logic straightforward without sacrificing flexibility.

### 4. Security by Default
All policies fail closed (deny by default), missing attributes result in access denial, and JWT tokens have limited lifespans.

## System Architecture

### High-Level Architecture

```mermaid
graph TD
    CA[Client Applications]
    LB[Load Balancer<br/>Traefik]
    CW[CIELO Web<br/>Django]
    AC[Azure Costs<br/>DRF]
    BA[Billing API<br/>DRF]
    IP[Identity Provider]
    PG[PostgreSQL<br/>Database]
    RD[Redis<br/>Cache]
    
    CA -->|HTTPS + JWT Cookie| LB
    LB --> CW
    LB --> AC
    LB --> BA
    CW --> IP
    AC --> IP
    BA --> IP
    IP --> PG
    IP --> RD
    
    style CA fill:#f9f,stroke:#333,stroke-width:2px
    style LB fill:#bbf,stroke:#333,stroke-width:2px
    style CW fill:#bfb,stroke:#333,stroke-width:2px
    style AC fill:#bfb,stroke:#333,stroke-width:2px
    style BA fill:#bfb,stroke:#333,stroke-width:2px
    style IP fill:#fbf,stroke:#333,stroke-width:2px
    style PG fill:#fbb,stroke:#333,stroke-width:2px
    style RD fill:#fbb,stroke:#333,stroke-width:2px
```

### Component Details

#### Identity Provider Service
- **Purpose**: Central authority for authentication and authorization
- **Responsibilities**:
  - User authentication API endpoints (`/api/login/`) for programmatic JWT token retrieval
  - Web-based login forms (`/login/`, `/logout/`) for browser SSO with JWT cookies
  - JWT token generation and validation
  - Service registration and manifest storage
  - Role and attribute management
  - Cache population and invalidation
- **Technology**: Django + Django REST Framework
- **Authentication Methods**:
  - **API Authentication**: POST to `/api/login/` with credentials returns JWT token
  - **Web SSO**: Form-based login at `/login/` sets httpOnly JWT cookie for domain-wide SSO
  - **Integration**: Other Django projects and applications consume authentication via JavaScript API calls

#### Redis Cache Layer
- **Purpose**: High-performance attribute storage
- **Features**:
  - Namespaced keys: `user:{id}:attrs:{service}`
  - TTL-based expiration (default: 300s)
  - Pub/Sub for real-time invalidation
  - Cluster support for scalability
- **Data Structure**:
  ```json
  {
    "user_id": 123,
    "username": "alice",
    "email": "alice@example.com",
    "roles": ["admin", "manager"],
    "department": "Engineering",
    "clearance_level": 4,
    "groups": ["dev", "ops"],
    "expires_at": "2024-12-31T23:59:59Z"
  }
  ```

#### Service Manifests
- **Purpose**: Service self-declaration of authorization needs
- **Structure**:
  ```python
  {
      "service": {
          "name": "unique_identifier",
          "display_name": "Human Name",
          "description": "Service purpose",
          "version": "1.0.0"
      },
      "roles": [
          {
              "name": "service_role",
              "display_name": "Role Name",
              "description": "Role purpose",
              "is_global": false,
              "default_expiry_days": 365
          }
      ],
      "attributes": [
          {
              "name": "attribute_name",
              "type": "string|integer|boolean|list",
              "required": false,
              "default": null,
              "description": "Attribute purpose"
          }
      ]
  }
  ```

#### Policy Engine
- **Purpose**: Evaluate authorization decisions
- **Implementation**: Strategy pattern with registry
- **Features**:
  - Decorator-based registration
  - Composable policies
  - Context-aware evaluation
  - Performance monitoring

## Data Flow

### Authentication Flow

There are two primary authentication flows:

#### 1. Web-Based SSO Authentication (Browser)
```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant IP as Identity Provider
    participant DB as Database
    participant R as Redis
    participant CW as CIELO/Other Apps
    
    U->>B: Navigate to protected page
    B->>CW: Request page (no JWT cookie)
    CW->>B: Redirect to Identity Provider
    B->>IP: GET /login/?redirect_uri=...
    IP->>B: Return login form
    U->>IP: Submit credentials
    IP->>DB: Validate Credentials
    DB-->>IP: User Valid
    IP->>IP: Generate JWT
    IP->>B: Set httpOnly JWT Cookie + Redirect
    IP->>R: Cache User Attributes
    B->>CW: Request with JWT Cookie
    CW-->>U: Protected Content
```

#### 2. API Authentication (JavaScript/Programmatic)
```mermaid
sequenceDiagram
    participant A as Application/JS
    participant IP as Identity Provider API
    participant DB as Database
    participant R as Redis
    
    A->>IP: POST /api/login/ {username, password}
    IP->>DB: Validate Credentials
    DB-->>IP: User Valid
    IP->>IP: Generate JWT
    IP->>R: Cache User Attributes
    IP-->>A: Return {token: "JWT..."}
    A->>A: Store token for API calls
    Note over A: Use token in Authorization header
```

### Authorization Flow
```mermaid
sequenceDiagram
    participant U as User
    participant SA as Service API
    participant JM as JWT Middleware
    participant R as Redis
    participant PE as Policy Engine
    
    U->>SA: API Request with JWT Cookie
    SA->>JM: Process Request
    JM->>JM: Extract user_id from JWT
    JM->>R: Get User Attributes
    R-->>JM: Return Cached Attributes
    JM->>PE: Evaluate ABAC Policy
    PE->>PE: Check Rules & Attributes
    PE-->>JM: Decision (Allow/Deny)
    alt Access Allowed
        JM->>SA: Continue Request
        SA-->>U: API Response
    else Access Denied
        JM-->>U: 403 Forbidden
    end
```

### Service Registration Flow
```mermaid
sequenceDiagram
    participant S as Service
    participant M as Manifest File
    participant IP as Identity Provider
    participant DB as Database
    
    S->>M: Read Service Manifest
    M-->>S: Return Manifest Data
    S->>IP: POST /api/services/register/
    Note over S,IP: Send manifest JSON
    IP->>IP: Validate Manifest
    alt Manifest Valid
        IP->>DB: Store Service Definition
        IP->>DB: Store Roles & Attributes
        DB-->>IP: Confirmation
        IP-->>S: Registration Success
    else Manifest Invalid
        IP-->>S: Validation Error
    end
```

## Integration Pattern for Django Projects

### Consuming Identity Provider Authentication

Django projects in the VF Services ecosystem integrate with the Identity Provider through:

1. **Frontend JavaScript API Calls**
   ```javascript
   // Example: Login via JavaScript
   fetch('https://identity.viloforge.com/api/login/', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({
       username: 'user@example.com',
       password: 'password'
     })
   })
   .then(response => response.json())
   .then(data => {
     // Store JWT token for subsequent API calls
     localStorage.setItem('jwt', data.token);
   });
   ```

2. **JWT Middleware Integration**
   - Services use the common JWT authentication middleware
   - Validates JWT tokens from cookies or Authorization headers
   - Extracts user context for authorization decisions

3. **No Direct Web Views**
   - Identity Provider does NOT expose application-specific web views
   - All authentication UI is either:
     - The Identity Provider's own login/logout forms
     - Custom forms in each Django project that call the API

## Design Patterns

### 1. Strategy Pattern (Policy Registry)
```python
# Registry maintains policy strategies
POLICY_REGISTRY = {}

def register_policy(name):
    def decorator(func):
        POLICY_REGISTRY[name] = func
        return func
    return decorator

# Policies are interchangeable strategies
@register_policy('ownership_check')
def ownership_check(user_attrs, obj=None, action=None):
    return obj.owner_id == user_attrs.user_id
```

### 2. Template Method (ABAC Mixin)
```python
class ABACModelMixin:
    """Template for ABAC-enabled models"""
    
    def check_abac(self, user_attrs, action):
        """Template method"""
        policy_name = self.get_policy_for_action(action)
        policy_func = self.get_policy_function(policy_name)
        return policy_func(user_attrs, self, action)
    
    def get_policy_for_action(self, action):
        """Hook for subclasses"""
        return self.ABAC_POLICIES.get(action)
```

### 3. Chain of Responsibility (Permission Classes)
```python
class CombinedPermission(BasePermission):
    """Chain multiple permission checks"""
    
    def __init__(self, *permissions, operator='AND'):
        self.permissions = permissions
        self.operator = operator
    
    def has_permission(self, request, view):
        if self.operator == 'AND':
            return all(p().has_permission(request, view) 
                      for p in self.permissions)
        else:  # OR
            return any(p().has_permission(request, view) 
                      for p in self.permissions)
```

### 4. Facade Pattern (Service Layer)
```python
class RBACService:
    """Simplified interface for complex RBAC operations"""
    
    def assign_role_to_user(self, user_id, role_name, service_name):
        # Complex logic hidden behind simple interface
        role = self._get_or_create_role(role_name, service_name)
        assignment = self._create_assignment(user_id, role)
        self._invalidate_cache(user_id, service_name)
        self._notify_services(user_id)
        return assignment
```

## Security Architecture

### Defense in Depth

1. **Network Layer**
   - TLS/SSL encryption for all traffic
   - Service mesh with mTLS between services
   - Firewall rules limiting service communication

2. **Application Layer**
   - JWT tokens with short expiration
   - CSRF protection on all forms
   - Input validation and sanitization
   - SQL injection prevention via ORM

3. **Authorization Layer**
   - Fail-closed policy evaluation
   - Principle of least privilege
   - Role expiration enforcement
   - Attribute validation

4. **Data Layer**
   - Encrypted data at rest
   - Column-level encryption for sensitive attributes
   - Audit logging for all changes
   - Regular backups with encryption

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Token theft | Short JWT expiration, HttpOnly cookies |
| Privilege escalation | Role expiration, audit logging |
| Cache poisoning | Redis AUTH, network isolation |
| Service impersonation | Service manifest validation |
| Replay attacks | JWT timestamp validation |
| Data leakage | Attribute filtering, encryption |

## Performance Considerations

### Caching Strategy

1. **Read-Through Cache**
   ```python
   def get_user_attributes(user_id, service_name):
       # Try cache first
       cached = redis_client.get(f"user:{user_id}:attrs:{service_name}")
       if cached:
           return cached
       
       # Cache miss - load from database
       attrs = load_from_database(user_id, service_name)
       redis_client.setex(
           f"user:{user_id}:attrs:{service_name}",
           ttl=300,
           value=attrs
       )
       return attrs
   ```

2. **Cache Invalidation**
   - Event-driven via Django signals
   - Pub/Sub for cross-service notification
   - TTL-based expiration as fallback

3. **Cache Warming**
   - Pre-populate on user login
   - Background jobs for active users
   - Lazy loading for inactive users

### Database Optimization

1. **Indexed Queries**
   ```sql
   CREATE INDEX idx_user_roles_user_service 
   ON user_roles(user_id, service_id, expires_at);
   
   CREATE INDEX idx_user_attributes_lookup 
   ON user_attributes(user_id, attribute_id);
   ```

2. **Query Optimization**
   ```python
   # Efficient: Single query with joins
   UserRole.objects.select_related('role__service').filter(
       user_id=user_id,
       service__name=service_name,
       expires_at__gt=timezone.now()
   )
   
   # Avoid: N+1 queries
   for role in user.roles.all():
       if role.service.name == service_name:
           # Process role
   ```

## Scalability Architecture

### Horizontal Scaling

1. **Stateless Services**
   - No session affinity required
   - Load balancer can distribute randomly
   - Easy to add/remove instances

2. **Redis Cluster**
   - Sharding by user_id
   - Read replicas for high availability
   - Sentinel for automatic failover

3. **Database Scaling**
   - Read replicas for queries
   - Connection pooling
   - Query result caching

### Vertical Scaling

1. **Resource Allocation**
   ```yaml
   # docker-compose.yml
   services:
     identity-provider:
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 2G
           reservations:
             cpus: '1.0'
             memory: 1G
   ```

2. **Performance Tuning**
   - Gunicorn worker processes
   - Database connection pools
   - Redis max memory settings

## Monitoring and Observability

### Metrics

1. **Authorization Metrics**
   - Policy evaluation time (p50, p95, p99)
   - Cache hit/miss rates
   - Permission denied rate by service
   - Active user sessions

2. **Performance Metrics**
   - API response times
   - Database query times
   - Redis operation latency
   - Service registration failures

### Logging

1. **Structured Logging**
   ```python
   logger.info("Authorization check", extra={
       "user_id": user_id,
       "service": service_name,
       "action": action,
       "policy": policy_name,
       "result": result,
       "duration_ms": duration
   })
   ```

2. **Audit Trail**
   - All role assignments/revocations
   - Attribute changes
   - Policy evaluation results
   - Service registrations

### Tracing

1. **Distributed Tracing**
   - OpenTelemetry integration
   - Trace ID propagation
   - Service dependency mapping

## Migration Strategy

### From Existing System

1. **Phase 1: Parallel Run**
   - Deploy RBAC-ABAC alongside existing auth
   - Mirror permissions in both systems
   - Compare authorization decisions

2. **Phase 2: Gradual Migration**
   - Migrate one service at a time
   - Start with low-risk services
   - Monitor for discrepancies

3. **Phase 3: Cutover**
   - Disable old authorization
   - Remove legacy code
   - Performance optimization

## Future Enhancements

### Planned Features

1. **Dynamic Policy Loading**
   - Hot reload policies without restart
   - Policy versioning and rollback
   - A/B testing for policies

2. **Machine Learning Integration**
   - Anomaly detection for access patterns
   - Predictive role assignments
   - Risk-based authentication

3. **Enhanced Federation**
   - SAML/OAuth2 support
   - External attribute providers
   - Cross-organization authorization

4. **Policy as Code**
   - Git-based policy management
   - Policy validation pipeline
   - Automated policy testing

## Conclusion

The VF Services RBAC-ABAC architecture provides a robust, scalable, and maintainable authorization system. By combining the simplicity of roles with the flexibility of attributes, it meets both current needs and future growth while maintaining high performance and security standards.