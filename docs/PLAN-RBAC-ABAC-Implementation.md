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
- Set up Redis ✅
- Create shared library structure ✅
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

## Implementation Status

### Phase 1: Infrastructure Setup ✅ COMPLETED

#### Step 1.1: Add Redis Service ✅
- Added Redis 7-alpine to docker-compose.yml
- Configured persistent storage with redisdata volume
- Added Redis environment variables to all services
- Added redis>=5.0.0 to requirements.txt

#### Step 1.2: Create Shared Library Structure ✅
- Created common/rbac_abac/ package structure
- Implemented core modules:
  - `__init__.py`: Package initialization and exports
  - `registry.py`: Policy registry with decorator pattern
  - `models.py`: UserAttributes data model
  - `redis_client.py`: Redis client for attribute caching
- Created comprehensive test suite:
  - `test_registry.py`: Tests for policy registration and execution
  - `test_models.py`: Tests for UserAttributes model
  - `test_redis_client.py`: Tests for Redis operations

### Phase 2: Core ABAC Components ✅ COMPLETED

#### Step 2.1: Implement Policy Registry ✅
- Created decorator-based policy registration system
- Global POLICY_REGISTRY for storing policies
- Support for policy listing and retrieval
- Comprehensive test coverage in test_registry.py

#### Step 2.2: Create ABACModelMixin ✅
- Implemented Template Method pattern for permission checks
- check_abac() method delegates to registered policies
- get_allowed_actions() for UI integration
- Dynamic policy selection support
- Metaclass validation for configuration
- Full test suite in test_mixins.py

#### Step 2.3: Implement Custom QuerySet ✅
- ABACQuerySet with abac_filter() method
- Database-level filtering for common policies
- Python-level fallback for complex policies
- ABACManager for easy model integration
- Convenience methods (viewable_by, editable_by)
- Comprehensive tests in test_querysets.py

#### Step 2.4: Create DRF Permission Classes ✅
- ABACPermission for object-level checks
- RoleRequired for simple role checks
- ServicePermission with auto-detection
- CombinedPermission for complex logic
- Request-level attribute caching
- Full test coverage in test_permissions.py

#### Additional: Default Policies ✅
- Created comprehensive set of default policies:
  - Ownership checks (ownership_check, ownership_or_admin)
  - Department policies (department_match, department_match_or_admin)
  - Group policies (group_membership, owner_or_group_admin)
  - Access policies (public_access, authenticated_only, admin_only)
  - Customer and document specific policies
  - Utility policies (read_only, deny_all)
- Composite policy builder for combining policies
- All policies tested in test_policies.py

### Phase 3: Identity Provider Extensions ✅ COMPLETED

#### Step 3.1: Add Role and Attribute Models ✅
- Created comprehensive Django models:
  - `Service`: Registered microservices
  - `Role`: Service-namespaced roles
  - `UserRole`: User-role assignments with expiration support
  - `ServiceAttribute`: Service-declared attributes
  - `UserAttribute`: User attribute values
  - `ServiceManifest`: Versioned service manifests
- Added Django admin interfaces for all models
- Full test coverage in test_models.py

#### Step 3.2: Implement Redis Population ✅
- Created services layer:
  - `RBACService`: Role management and queries
  - `AttributeService`: Attribute management
  - `RedisService`: Redis cache population and invalidation
  - `ManifestService`: Service manifest registration
- Implemented Django signals for automatic cache updates:
  - UserRole changes trigger cache invalidation/repopulation
  - UserAttribute changes update relevant service caches
  - Service activation/deactivation handles bulk updates
  - User detail changes propagate to all services
- Connected signals in app configuration
- Comprehensive test suite in test_services.py

### Phase 4: Service Integration ✅ COMPLETED

#### Step 4.1: Create Manifest Registration API ✅ COMPLETED
**Status**: Completed
**Implementation Details**:
- Created POST /api/services/register/ endpoint in Identity Provider
- Added ServiceRegisterView class with comprehensive request validation:
  - Validates service name format (lowercase, alphanumeric with hyphens/underscores)
  - Validates role names and structure
  - Validates attribute names and types
  - Checks all required fields are present
- Integrated with ManifestService for manifest processing
- Added comprehensive Swagger/OpenAPI documentation
- Updated API info endpoint to include new registration endpoint
- Currently using AllowAny permission (service-to-service auth to be added later)

#### Step 4.2: Update JWT Middleware ✅ COMPLETED
**Status**: Completed
**Implementation Details**:
- Modified `common/jwt_auth/middleware.py` to load user attributes after JWT validation
- Added `_load_user_attributes()` method that:
  - Imports `get_user_attributes` locally to avoid circular imports
  - Loads attributes from Redis using user ID and SERVICE_NAME
  - Adds attributes to request as `request.user_attrs`
  - Handles ImportError and general exceptions gracefully
  - Includes performance logging when DEBUG level is enabled
- Attributes are only loaded if user has an ID and SERVICE_NAME is configured

#### Step 4.3: Create Example Models ✅ COMPLETED
**Status**: Completed
**Implementation Details**:

**Billing API**:
- Added SERVICE_NAME = 'billing_api' to settings
- Created comprehensive billing models with ABAC:
  - Customer: With department-based and customer_ids access control
  - Invoice: With viewing, editing, sending, and cancellation policies
  - Payment: With processing and refund policies
  - Subscription: With management and renewal policies
- Created billing-specific policies in `billing/policies.py`
- Created service manifest with 11 roles and 5 attributes
- Updated BillingConfig to register policies on startup

**Inventory API**:
- Added SERVICE_NAME = 'inventory_api' to settings
- Created comprehensive inventory models with ABAC:
  - Category: Public viewing with managed editing
  - Warehouse: Department and manager-based access
  - Product: Department-based viewing with creator privileges
  - StockLevel: Warehouse-based access control
  - StockMovement: Multi-warehouse access patterns
  - InventoryCount: Assignment and warehouse-based access
- Created inventory-specific policies in `inventory/policies.py`
- Created service manifest with 18 roles and 6 attributes
- Updated InventoryConfig to register policies on startup

Both services now have:
- ABACModelMixin on all protected models
- ABACManager for filtered querysets
- Custom policies for business-specific rules
- Service manifests ready for registration
- Automatic policy loading on startup

### Phase 5: Management and Monitoring ✅ PARTIALLY COMPLETED

#### Step 5.1: Create Management APIs ⚠️ PARTIAL
**Completed**:
- Setup demo users command (`setup_demo_users`)
- Complete demo setup command (`complete_demo_setup`)
- Refresh cache command (`refresh_demo_cache`)
- Django admin interface for role/attribute management

**Still Needed**:
- RESTful API endpoints for role assignment
- RESTful API endpoints for attribute management
- Bulk operations support
- Comprehensive audit logging

#### Step 5.2: Add Monitoring ✅ COMPLETED
**Completed**:
- Interactive demo dashboard with setup status
- RBAC dashboard showing live permissions from Redis
- API Explorer for testing endpoints with different users
- Permission matrix visualization
- Access playground with pre-configured scenarios
- Real-time Redis data display
- Management commands for cache refresh

**Implementation Details**:
- Created comprehensive demo pages in website service:
  - `/demo/` - Main dashboard with system status
  - `/demo/rbac/` - User permissions and attributes viewer
  - `/demo/api/` - Interactive API testing interface
  - `/demo/matrix/` - Visual permission matrix
  - `/demo/playground/` - Scenario-based testing
- Added demo user switching without logout
- Integrated JWT token management
- Real-time permission verification

See [RBAC-ABAC Demo Pages Guide](docs/RBAC-ABAC-DEMO-PAGES.md) for full documentation.

## Current Status Summary

### ✅ Completed
1. **Infrastructure** (Phase 1): Redis setup, shared library structure
2. **Core Components** (Phase 2): Policy registry, model mixins, querysets, permissions
3. **Identity Provider** (Phase 3): Models, services, signals, admin interface
4. **Service Integration** (Phase 4): 
   - JWT middleware enhancement for attribute loading
   - Manifest registration API endpoint
   - Example implementations in both billing and inventory services
5. **Monitoring** (Phase 5.2): 
   - Interactive demo pages for testing and visualization
   - Real-time permission monitoring
   - Management commands for maintenance

### ⚠️ Partially Completed
1. **Management APIs** (Phase 5.1): 
   - Django admin interface available
   - Management commands implemented
   - RESTful APIs still needed

### 🚀 Next Steps
1. Add RESTful management APIs for roles and attributes
2. Implement comprehensive audit logging
3. Add bulk operations support
4. Create performance metrics dashboard
5. Document production deployment considerations

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