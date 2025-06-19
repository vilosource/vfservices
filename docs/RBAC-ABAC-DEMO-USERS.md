# RBAC-ABAC Demo Users Guide

This document describes the demo users for showcasing the RBAC-ABAC (Role-Based and Attribute-Based Access Control) implementation in VF Services.

## Overview

Four demo users demonstrate different access patterns across the microservices architecture:
- **Alice**: Senior Manager with cross-functional access
- **Bob**: Billing Specialist with finance focus
- **Charlie**: Cloud Infrastructure Manager with operations focus  
- **David**: Customer Service Representative with limited read access

### Interactive Testing
These demo users can be tested interactively using the web-based demo pages:
- **Demo Dashboard** (`/demo/`): Switch between users instantly
- **RBAC Dashboard** (`/demo/rbac/`): View each user's permissions
- **API Explorer** (`/demo/api/`): Test API access with each user
- **Permission Matrix** (`/demo/matrix/`): See all role assignments
- **Access Playground** (`/demo/playground/`): Run pre-configured scenarios

See the [Demo Pages Guide](./RBAC-ABAC-DEMO-PAGES.md) for detailed instructions.

## User Personas and Access Rights

### 1. Alice - Senior Manager

**Profile**
- **Username**: `alice`
- **Email**: `alice@vfservices.com`
- **Department**: Management
- **Responsibilities**: Oversees billing and cloud infrastructure operations across the organization

**Roles**
| Service | Role | Description |
|---------|------|-------------|
| Billing API | `billing_admin` | Full control over all billing operations |
| Inventory API | `inventory_manager` | Can manage cloud resources but not admin functions |
| Identity Provider | `customer_manager` | Can manage customer relationships |

**Attributes**
```json
{
  "department": "Management",
  "customer_ids": [100, 200, 300, 400, 500],
  "warehouse_ids": [1, 2],  // Region IDs: 1=us-east-1, 2=eu-west-1
  "invoice_limit": 50000,
  "max_refund_amount": 10000,
  "can_export_data": true
}
```

**Access Capabilities**
- Create, approve, and delete invoices up to $50,000
- Approve refunds up to $10,000
- Manage cloud resources in regions 1 (us-east-1) and 2 (eu-west-1)
- Export data from both billing and cloud inventory systems
- Access all customers (100-500)

---

### 2. Bob - Billing Specialist

**Profile**
- **Username**: `bob`
- **Email**: `bob@vfservices.com`
- **Department**: Finance
- **Responsibilities**: Handles invoicing and payments for specific customers

**Roles**
| Service | Role | Description |
|---------|------|-------------|
| Billing API | `invoice_manager` | Can create and manage invoices |
| Billing API | `payment_processor` | Can process payments |
| Billing API | `invoice_sender` | Can send invoices to customers |
| Inventory API | `stock_viewer` | Read-only access to cloud resources for billing purposes |

**Attributes**
```json
{
  "department": "Finance",
  "customer_ids": [100, 200, 300],
  "invoice_limit": 5000,
  "payment_methods": ["credit_card", "bank_transfer"],
  "max_refund_amount": 1000
}
```

**Access Capabilities**
- Create and manage invoices up to $5,000
- Process payments via credit card and bank transfer
- Approve refunds up to $1,000
- View cloud resource allocations (read-only)
- Access customers 100, 200, and 300 only

---

### 3. Charlie - Cloud Infrastructure Manager

**Profile**
- **Username**: `charlie`
- **Email**: `charlie@vfservices.com`
- **Department**: Operations
- **Responsibilities**: Manages cloud resources in region 1 (us-east-1)

**Roles**
| Service | Role | Description |
|---------|------|-------------|
| Inventory API | `warehouse_manager` | Full control of assigned region/datacenter |
| Inventory API | `stock_adjuster` | Can adjust resource allocations |
| Inventory API | `movement_approver` | Can approve resource migrations |
| Inventory API | `count_supervisor` | Oversees resource audits |

**Attributes**
```json
{
  "department": "Operations",
  "warehouse_ids": [1],  // Region ID: 1=us-east-1
  "product_categories": ["compute", "storage"],
  "max_adjustment_value": 5000,
  "movement_types": ["migration", "decommission", "reallocation"],
  "can_export_data": false
}
```

**Access Capabilities**
- Full control over region 1 (us-east-1) cloud resources
- Adjust resource allocations up to $5,000 in value
- Approve resource migrations, decommissions, and reallocations
- Manage compute and storage resource categories only
- No access to billing systems
- Cannot export data

---

### 4. David - Customer Service Representative

**Profile**
- **Username**: `david`
- **Email**: `david@vfservices.com`
- **Department**: Support
- **Responsibilities**: Handles customer inquiries across systems

**Roles**
| Service | Role | Description |
|---------|------|-------------|
| Billing API | `invoice_viewer` | Can view invoices |
| Billing API | `payment_viewer` | Can view payment status |
| Inventory API | `product_viewer` | Can view cloud service catalog |
| Inventory API | `stock_viewer` | Can check resource availability |

**Attributes**
```json
{
  "department": "Support",
  "customer_ids": [100],
  "warehouse_ids": [],
  "invoice_limit": 0,
  "can_export_data": false
}
```

**Access Capabilities**
- View invoices and payments for customer 100 only
- Check cloud service catalog and resource availability
- Cannot create or modify any data
- Cannot export data
- No warehouse access

## Demo Scenarios

### Scenario 1: Invoice Management
Demonstrates role-based access to invoice operations:

1. **Alice** creates a $30,000 invoice for customer 200 ✅
2. **Bob** creates a $4,000 invoice for customer 100 ✅
3. **Bob** attempts to create a $6,000 invoice ❌ (exceeds limit)
4. **Charlie** attempts to view invoices ❌ (no billing access)
5. **David** views invoice for customer 100 ✅
6. **David** attempts to view invoice for customer 200 ❌ (not assigned)

### Scenario 2: Cloud Resource Management
Shows region and resource category restrictions:

1. **Alice** adjusts resource allocation in region 1 (us-east-1) ✅
2. **Alice** adjusts resource allocation in region 2 (eu-west-1) ✅
3. **Bob** views resource usage in region 1 ✅
4. **Bob** attempts to adjust resources ❌ (read-only)
5. **Charlie** adjusts compute resources in region 1 ✅
6. **Charlie** attempts to adjust resources in region 2 ❌ (not assigned)

### Scenario 3: Cross-Service Integration
Demonstrates service-level access control:

1. **Alice** accesses billing admin panel ✅
2. **Alice** accesses inventory management panel ✅
3. **Bob** accesses billing operations ✅
4. **Bob** attempts resource adjustments ❌ (viewer only)
5. **Charlie** accesses cloud resource operations ✅
6. **Charlie** attempts to access billing ❌ (no roles)

### Scenario 4: Attribute-Based Restrictions
Shows how attributes control access:

1. **Department-based**: Only Finance dept (Bob) can process refunds
2. **Customer-based**: Bob can't access customer 400 data
3. **Region-based**: Charlie limited to region 1 (us-east-1)
4. **Value-based**: Bob's $5,000 invoice limit enforced

### Scenario 5: Time-Based Permissions
Demonstrates temporary role assignments:

```python
# Bob gets temporary billing_admin for 7 days (covering for Alice)
UserRole.objects.create(
    user=bob,
    role=billing_admin_role,
    granted_by=alice,
    expires_at=timezone.now() + timedelta(days=7),
    reason="Covering for Alice - vacation"
)

# David gets temporary invoice_manager for customer 200 for 24 hours
UserRole.objects.create(
    user=david,
    role=invoice_manager_role,
    granted_by=alice,
    resource_id="customer_200",
    expires_at=timezone.now() + timedelta(hours=24),
    reason="Urgent customer escalation"
)
```

## Implementation Guide

### Step 1: Create User Accounts

```python
# Django management command or shell
from django.contrib.auth.models import User

# Create users
alice = User.objects.create_user(
    username='alice',
    email='alice@vfservices.com',
    password='alice123',
    first_name='Alice',
    last_name='Manager'
)

bob = User.objects.create_user(
    username='bob',
    email='bob@vfservices.com',
    password='bob123',
    first_name='Bob',
    last_name='Billing'
)

charlie = User.objects.create_user(
    username='charlie',
    email='charlie@vfservices.com',
    password='charlie123',
    first_name='Charlie',
    last_name='Warehouse'
)

david = User.objects.create_user(
    username='david',
    email='david@vfservices.com',
    password='david123',
    first_name='David',
    last_name='Support'
)
```

### Step 2: Register Services

Ensure both services have registered their manifests:

```bash
# Billing API should auto-register on startup
# Inventory API should auto-register on startup
# Verify in Django admin or via API
```

### Step 3: Assign Roles

```python
from identity_app.models import Service, Role, UserRole

# Get services
billing_service = Service.objects.get(name='billing_api')
inventory_service = Service.objects.get(name='inventory_api')

# Get roles
billing_admin = Role.objects.get(service=billing_service, name='billing_admin')
invoice_manager = Role.objects.get(service=billing_service, name='invoice_manager')
# ... (get all required roles)

# Assign roles to Alice
UserRole.objects.create(user=alice, role=billing_admin, granted_by=admin)
UserRole.objects.create(user=alice, role=inventory_manager, granted_by=admin)
UserRole.objects.create(user=alice, role=customer_manager, granted_by=admin)

# Assign roles to Bob
UserRole.objects.create(user=bob, role=invoice_manager, granted_by=admin)
UserRole.objects.create(user=bob, role=payment_processor, granted_by=admin)
# ... (continue for all users)
```

### Step 4: Set User Attributes

```python
from identity_app.models import ServiceAttribute, UserAttribute
import json

# Get attribute definitions
dept_attr = ServiceAttribute.objects.get(name='department')
customer_ids_attr = ServiceAttribute.objects.get(name='customer_ids')
# ... (get all attributes)

# Set Alice's attributes
UserAttribute.objects.create(
    user=alice,
    attribute=dept_attr,
    value='Management'
)
UserAttribute.objects.create(
    user=alice,
    attribute=customer_ids_attr,
    value=json.dumps([100, 200, 300, 400, 500])
)
# ... (set all attributes for all users)
```

### Step 5: Create Test Data

```python
# In billing-api
from billing.models import Invoice, Customer

customer_100 = Customer.objects.create(id=100, name="Acme Corp")
customer_200 = Customer.objects.create(id=200, name="Tech Solutions")

# In inventory-api
from inventory.models import Warehouse, Product

warehouse_1 = Warehouse.objects.create(id=1, name="US East 1 (us-east-1)")
warehouse_2 = Warehouse.objects.create(id=2, name="EU West 1 (eu-west-1)")
```

## Testing the Implementation

### Interactive Web Testing

The easiest way to test the implementation is through the demo pages:

1. Navigate to `http://website.vfservices.viloforge.com/demo/`
2. Use the user switcher to change between demo users
3. Test API endpoints in the API Explorer
4. View real-time permissions in the RBAC Dashboard
5. Run scenarios in the Access Playground

### API Authentication

For programmatic testing, authenticate to get a JWT token:

```bash
# Login as Alice
curl -X POST http://localhost:8100/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "alice123"}'

# Response: {"token": "eyJ..."}
```

### Testing Access Control

```bash
# Alice creating a high-value invoice (should succeed)
curl -X POST http://localhost:8200/api/invoices/ \
  -H "Authorization: Bearer <alice_token>" \
  -H "Content-Type: application/json" \
  -d '{"customer_id": 200, "amount": 30000, "description": "Enterprise License"}'

# Bob accessing customer outside his scope (should fail)
curl -X GET http://localhost:8200/api/customers/400/ \
  -H "Authorization: Bearer <bob_token>"
# Response: 403 Forbidden

# Charlie accessing billing API (should fail)
curl -X GET http://localhost:8200/api/invoices/ \
  -H "Authorization: Bearer <charlie_token>"
# Response: 403 Forbidden
```

## Monitoring and Debugging

### Web-Based Monitoring

Use the demo pages for real-time monitoring:
- **RBAC Dashboard** (`/demo/rbac/`): Shows live Redis data for each user
- **API Explorer** (`/demo/api/`): Test permissions with instant feedback
- **Permission Matrix** (`/demo/matrix/`): Visual overview of all assignments

### Management Commands

```bash
# Refresh Redis cache for all demo users
python manage.py refresh_demo_cache

# Re-run complete demo setup if needed
python manage.py complete_demo_setup
```

### Check User Permissions (Django Shell)

```python
# Django shell
from common.rbac_abac import get_user_attributes

# Check Alice's complete permission set
alice_attrs = get_user_attributes(alice.id)
print(f"Roles: {alice_attrs.roles}")
print(f"Department: {alice_attrs.department}")
print(f"Customer IDs: {alice_attrs.customer_ids}")
```

### View Redis Cache

```bash
# Check cached attributes
redis-cli
> GET "user_attrs:1"  # Alice's user ID
```

### Audit Trail

All role assignments and changes are logged:
- Who granted the role
- When it was granted
- Expiration date (if any)
- Reason for assignment

## Best Practices

1. **Principle of Least Privilege**: Users have minimum required access
2. **Separation of Duties**: Billing and warehouse operations are separated
3. **Attribute-Based Refinement**: Roles are refined with attributes
4. **Time-Bound Access**: Temporary permissions expire automatically
5. **Audit Trail**: All permission changes are logged

## Troubleshooting

### Common Issues

1. **User can't access expected resource**
   - Check role assignments
   - Verify attributes are set correctly
   - Check for expired roles
   - Verify service registration

2. **Slow permission checks**
   - Check Redis connectivity
   - Verify attribute caching
   - Monitor service communication

3. **Inconsistent permissions**
   - Clear Redis cache
   - Reload user attributes
   - Check for service registration issues

## Extending the Demo

To add more scenarios:

1. **Add New User**: Create user with unique role/attribute combination
2. **Add New Role**: Update service manifest and re-register
3. **Add New Attribute**: Define in manifest with validation rules
4. **Create Policy**: Implement custom policy for complex rules

## Notes on Terminology

The inventory service uses traditional inventory terminology (warehouse, stock, product) but manages cloud resources:
- **Warehouse** = Cloud Region/Datacenter (e.g., us-east-1, eu-west-1)
- **Product** = Cloud Service/Resource Type (e.g., compute instances, storage volumes)
- **Stock** = Available Resource Capacity
- **Movement** = Resource Migration/Reallocation
- **Categories** = Resource Types (compute, storage, network, etc.)

## Conclusion

These demo users provide a comprehensive showcase of the RBAC-ABAC system's capabilities, demonstrating:
- Role-based access control
- Attribute-based refinements
- Cross-service authorization
- Time-based permissions
- Hierarchical access patterns

Use these users to test, demonstrate, and validate the access control implementation across VF Services.