# PLAN: RBAC-ABAC Implementation for VF Services

## Executive Summary

This document outlines the implementation plan for a hybrid Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) system for the VF Services microservices architecture. The system will provide fine-grained, scalable authorization while maintaining service autonomy and following SOLID principles.

## Why: The Need for RBAC-ABAC

### Current State
- VF Services has basic JWT authentication with minimal tokens
- No authorization system beyond Django's IsAuthenticated
- Each service (Identity Provider, Website, Billing API, Inventory API) operates independently
- No mechanism for role-based or context-aware permissions

### Problems to Solve
1. **Scalability**: Need authorization that scales across multiple microservices without creating bottlenecks
2. **Flexibility**: Simple role checks (RBAC) aren't sufficient for complex business rules like "users can only edit documents in their department"
3. **Maintainability**: Authorization logic scattered across services leads to inconsistency and duplication
4. **Performance**: Avoiding repeated database queries for permission checks across services
5. **Service Autonomy**: Each service team needs to manage their own authorization rules without modifying central services

### Benefits of Our Approach
- **Hybrid Model**: Combines simple role checks (RBAC) with context-aware attribute rules (ABAC)
- **Distributed Authorization**: Each service enforces its own rules, avoiding central bottlenecks
- **Cached Attributes**: Redis provides millisecond-latency access to user roles/attributes
- **Extensible Design**: New services, roles, and policies can be added without modifying existing code
- **SOLID Compliance**: Clean separation of concerns, open for extension, closed for modification

## What: System Architecture Overview

### Core Components

1. **Redis Cache Layer**
   - Central attribute store for user roles and attributes
   - Pub/Sub for real-time invalidation
   - Namespaced by service (e.g., `user:123:roles:billing_api`)

2. **Shared RBAC-ABAC Library**
   - Policy Registry: Decorator-based registration of authorization rules
   - ABACModelMixin: Django model mixin for permission checks
   - Custom QuerySet: Database-level filtering for performance
   - DRF Permissions: Integration with Django REST Framework

3. **Identity Provider Extensions**
   - Role and UserAttribute models
   - Service manifest registration endpoint
   - Redis population on changes
   - Role/attribute management APIs

4. **Service-Level Implementation**
   - Service manifests declaring roles/attributes
   - Models using ABACModelMixin
   - Custom policies for business rules
   - ViewSets with ABAC permissions

### Data Flow
1. User authenticates → receives minimal JWT (user ID + expiry)
2. Service receives request → validates JWT
3. Service loads user attributes from Redis cache
4. Service checks permissions using local policy functions
5. Service returns filtered/authorized data

## How: Implementation Steps

### Phase 1: Infrastructure Setup

#### Step 1.1: Add Redis Service
**Why**: Redis provides the fast, distributed cache needed for attribute storage and pub/sub messaging.

**What**: Add Redis container to docker-compose.yml with persistent storage and network configuration.

**How**:
- Add Redis 7.x service to docker-compose.yml
- Configure persistent volume for data
- Set up network access for all services
- Add Redis connection settings to Django settings

#### Step 1.2: Create Shared Library Structure
**Why**: Common authorization code should be implemented once and shared across all services.

**What**: Create `common/rbac_abac/` package with core authorization components.

**How**:
- Create Python package structure
- Set up module imports
- Configure as installable package for services
- Add to requirements.txt for each service

### Phase 2: Core ABAC Components

#### Step 2.1: Implement Policy Registry
**Why**: Policies need to be pluggable and discoverable without hardcoding.

**What**: Registry pattern with decorator-based registration of policy functions.

**How**:
```python
# Global registry
POLICY_REGISTRY = {}

# Decorator for registration
@register_policy('ownership_check')
def ownership_check(user_attrs, obj, action):
    return obj.owner_id == user_attrs.user_id
```

#### Step 2.2: Create ABACModelMixin
**Why**: Django models need a consistent interface for permission checks.

**What**: Mixin providing `check_abac()` method that delegates to registered policies.

**How**:
- Implement check_abac() method
- Support policy mapping (action → policy name)
- Template Method pattern for extensibility
- Error handling for missing policies

#### Step 2.3: Implement Custom QuerySet
**Why**: List endpoints need efficient database-level filtering, not post-fetch filtering.

**What**: QuerySet with `abac_filter()` method that translates policies to SQL.

**How**:
- Extend Django QuerySet
- Implement abac_filter() method
- Translate common policies to Q objects
- Fallback for complex policies

#### Step 2.4: Create DRF Permission Classes
**Why**: API endpoints need to enforce ABAC rules consistently.

**What**: Custom permission classes that use model's check_abac() method.

**How**:
- Extend BasePermission
- Implement has_permission() for view-level checks
- Implement has_object_permission() for object-level
- Map HTTP methods to actions

### Phase 3: Identity Provider Extensions

#### Step 3.1: Add Role and Attribute Models
**Why**: Need persistent storage for roles and user attributes.

**What**: Django models for Role, UserRole, UserAttribute with service namespacing.

**How**:
```python
class Role(models.Model):
    service = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    description = models.TextField()
    
class UserRole(models.Model):
    user = models.ForeignKey(User)
    role = models.ForeignKey(Role)
    resource_id = models.CharField(null=True)  # For scoped roles
```

#### Step 3.2: Implement Redis Population
**Why**: Changes to roles/attributes must propagate to cache immediately.

**What**: Django signals and methods to update Redis on model changes.

**How**:
- Use post_save signals on role/attribute models
- Implement Redis update methods
- Add pub/sub notifications for cache invalidation
- Handle batch updates efficiently

#### Step 3.3: Create Manifest Registration
**Why**: Services need to declare their authorization requirements without code changes to IDP.

**What**: API endpoint for services to register their manifest on startup.

**How**:
- POST /api/services/register endpoint
- Idempotent upsert logic
- Validate manifest schema
- Update Role and attribute definitions

### Phase 4: Service Integration

#### Step 4.1: Update JWT Middleware
**Why**: Need to load user attributes after JWT validation.

**What**: Extend existing JWT middleware to fetch attributes from Redis.

**How**:
- After JWT validation, load attributes from Redis
- Add attributes to request.user_attrs
- Handle cache misses gracefully
- Add performance logging

#### Step 4.2: Create Service Manifests
**Why**: Each service needs to declare its roles and required attributes.

**What**: JSON manifest files for each service.

**How**:
```json
{
  "service": "billing_api",
  "roles": [
    {"name": "billing_admin", "description": "Full billing access"},
    {"name": "invoice_viewer", "description": "Can view invoices"}
  ],
  "attributes": [
    {"name": "department", "description": "User's department"},
    {"name": "customer_ids", "description": "Accessible customer IDs"}
  ]
}
```

#### Step 4.3: Implement Example Models
**Why**: Demonstrate ABAC usage and provide templates for teams.

**What**: Sample models in each service using ABACModelMixin.

**How**:
- Create Invoice model in billing_api with ABAC
- Create Product model in inventory_api with ABAC
- Define appropriate policies for each
- Document usage patterns

### Phase 5: Management and Monitoring

#### Step 5.1: Create Management APIs
**Why**: Administrators need to manage roles and attributes.

**What**: RESTful APIs in Identity Provider for role/attribute CRUD.

**How**:
- Role assignment endpoints
- Attribute management endpoints
- Bulk operations support
- Audit logging

#### Step 5.2: Add Monitoring
**Why**: Need visibility into authorization decisions and performance.

**What**: Logging and metrics for authorization checks.

**How**:
- Log denied access attempts
- Track policy execution times
- Monitor Redis cache hit rates
- Create dashboards for visibility

## Implementation Timeline

### Week 1-2: Infrastructure and Core Library
- Set up Redis
- Create shared library structure
- Implement policy registry and model mixin

### Week 3-4: Identity Provider Extensions
- Add role/attribute models
- Implement Redis population
- Create manifest registration

### Week 5-6: Service Integration
- Update JWT middleware
- Integrate with one service (billing_api) as pilot
- Create example models and policies

### Week 7-8: Rollout and Documentation
- Integrate remaining services
- Create management APIs
- Write documentation and training materials

## Risk Mitigation

### Performance Risks
- **Risk**: Redis becomes bottleneck
- **Mitigation**: Local caching with TTL, read replicas if needed

### Consistency Risks
- **Risk**: Stale permissions in cache
- **Mitigation**: Pub/sub invalidation, short TTLs, audit logging

### Complexity Risks
- **Risk**: Policy logic becomes too complex
- **Mitigation**: Policy testing framework, clear patterns, documentation

## Success Criteria

1. All services use RBAC-ABAC for authorization
2. Sub-10ms authorization checks for 95% of requests
3. New services can onboard without central code changes
4. Clear audit trail of authorization decisions
5. Development teams can manage their own policies

## Next Steps

1. Review and approve this plan
2. Set up development environment with Redis
3. Begin Phase 1 implementation
4. Schedule weekly progress reviews

## Appendix: Code Examples

### Policy Function Example
```python
@register_policy('department_match')
def department_match(user_attrs, obj, action):
    """User can only access objects in their department"""
    return user_attrs.department == obj.department
```

### Model with ABAC Example
```python
class Invoice(ABACModelMixin, models.Model):
    customer = models.ForeignKey(Customer)
    department = models.CharField(max_length=50)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    ABAC_POLICIES = {
        'view': 'department_match',
        'edit': 'billing_admin_only',
        'delete': 'billing_admin_only'
    }
```

### ViewSet with ABAC Example
```python
class InvoiceViewSet(ModelViewSet):
    queryset = Invoice.objects.all()
    permission_classes = [ABACPermission]
    
    def get_queryset(self):
        user_attrs = self.request.user_attrs
        return Invoice.objects.abac_filter(user_attrs, 'view')
```