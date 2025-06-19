# RBAC-ABAC Testing Guide

## Overview

This guide explains how to test the RBAC-ABAC system and interpret the results correctly.

## Understanding the Demo Users

Each demo user has specific roles that determine what they can access:

| User | Role | Department | Primary Responsibilities |
|------|------|------------|-------------------------|
| Alice | Senior Manager | Management | Billing administration, Customer management |
| Bob | Billing Specialist | Finance | Invoice management, Payment processing |
| Charlie | Cloud Infrastructure Manager | Operations | Warehouse management (Region 1 only) |
| David | Customer Service Rep | Support | Read-only access to customer 100 |

## Expected Test Results

### Alice's Access Pattern

**What Alice CAN do:**
- ✅ Access `/billing-admin/` endpoints (has `billing_admin` role)
- ✅ Access `/customer-manager/` endpoints (has `customer_manager` role)  
- ✅ View and manage all customer data (100-500)
- ✅ Approve transactions up to $50,000

**What Alice CANNOT do:**
- ❌ Access `/invoice-manager/` endpoints (Bob's role)
- ❌ Access `/payment-processor/` endpoints (Bob's role)
- ❌ Access warehouse management (Charlie's role)

**This is correct behavior!** Alice is a senior manager but doesn't have invoice management permissions - that's delegated to Bob.

### Bob's Access Pattern

**What Bob CAN do:**
- ✅ Access `/invoice-manager/` endpoints
- ✅ Access `/payment-processor/` endpoints
- ✅ Create invoices up to $5,000
- ✅ Process credit card and bank transfer payments

**What Bob CANNOT do:**
- ❌ Access `/billing-admin/` endpoints (Alice's role)
- ❌ Access `/customer-manager/` endpoints (Alice's role)
- ❌ Approve high-value transactions over $5,000

### Testing Procedure

1. **Login as Demo User**
   ```
   Navigate to: https://website.vfservices.viloforge.com/demo/
   Select user from dropdown (e.g., Alice)
   ```

2. **Check API Explorer**
   ```
   Go to: API Explorer
   Test various endpoints
   Note which return 200 OK vs 403 Forbidden
   ```

3. **Verify Permissions**
   ```
   Go to: RBAC Dashboard
   Check "Actual Permissions" section
   Compare with "Expected Permissions"
   ```

## Common Misconceptions

### "Alice should have access to everything"
**Reality**: Senior managers have specific delegated responsibilities. Alice manages billing administration and customers, but invoice processing is delegated to specialists.

### "403 Forbidden means something is broken"
**Reality**: 403 responses are correct when users lack required roles. This demonstrates the security system working properly.

### "All billing endpoints should be accessible to billing users"
**Reality**: Billing is subdivided into specific roles:
- `billing_admin`: High-level administration
- `invoice_manager`: Invoice creation and editing
- `payment_processor`: Payment handling
- `invoice_viewer`: Read-only access

## Testing Checklist

- [ ] Each user can log in successfully
- [ ] JWT tokens are generated with user_id
- [ ] Redis cache is populated after login
- [ ] Role-specific endpoints return 200 for authorized users
- [ ] Role-specific endpoints return 403 for unauthorized users
- [ ] User attributes are loaded correctly
- [ ] Attribute-based filtering works (e.g., customer_ids)

## Debugging Failed Tests

### User gets 403 on expected endpoint

1. **Check role assignment**:
   ```bash
   docker exec -it vfservices-identity-provider-1 python manage.py shell
   from django.contrib.auth.models import User
   from identity_app.models import UserRole
   user = User.objects.get(username='alice')
   UserRole.objects.filter(user=user).values_list('role__name', flat=True)
   ```

2. **Check Redis cache**:
   ```bash
   docker exec -it vfservices-redis-1 redis-cli
   GET user:4:attrs:billing_api  # Adjust user ID
   ```

3. **Check service logs**:
   ```bash
   docker logs vfservices-billing-api-1 | grep "Permission check"
   ```

### User gets 200 on unexpected endpoint

1. **Verify endpoint permissions**:
   Check the view's permission_classes
   
2. **Check for role overlap**:
   Some roles may grant broader access than expected

## Success Criteria

The RBAC-ABAC system is working correctly when:

1. ✅ Each user can only access endpoints for their assigned roles
2. ✅ 403 Forbidden is returned for unauthorized access attempts
3. ✅ User attributes are available in request.user_attrs
4. ✅ Attribute-based filtering limits data access appropriately
5. ✅ Redis cache is populated and used for performance

## Example Test Session

```
1. Login as Alice
2. Test /api/billing-admin/ → Expect: 200 OK ✅
3. Test /api/invoice-manager/ → Expect: 403 Forbidden ✅
4. Test /api/customer/200/ → Expect: 200 OK (in customer_ids) ✅
5. Test /api/customer/600/ → Expect: 403 Forbidden (not in customer_ids) ✅

Result: System working correctly!
```

Remember: Access denial is not a bug - it's the security system protecting resources according to the defined business rules.