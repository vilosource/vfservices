# VF Services Developer Documentation

Complete technical documentation for the VF Services platform, covering authentication, authorization, and cross-service integration.

## 📚 Documentation Index

### JWT Authentication
| Document | Purpose | Audience |
|----------|---------|----------|
| **[JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)** | Complete JWT implementation guide | New service developers |
| **[JWT Quick Reference](./JWT-AUTH-QUICK-REFERENCE.md)** | Copy-paste patterns and examples | Experienced developers |
| **[JWT Troubleshooting](./JWT-AUTH-TROUBLESHOOTING.md)** | Common issues and solutions | All developers |

### RBAC-ABAC Authorization
| Document | Purpose | Audience |
|----------|---------|----------|
| **[RBAC-ABAC Developer Guide](./RBAC-ABAC-DEVELOPER-GUIDE.md)** | Comprehensive authorization guide | New service developers |
| **[RBAC-ABAC Quick Reference](./RBAC-ABAC-QUICK-REFERENCE.md)** | Quick patterns and examples | Experienced developers |
| **[RBAC-ABAC Architecture](./RBAC-ABAC-ARCHITECTURE.md)** | System design and patterns | Architects & senior devs |

## 🚀 Quick Start Paths

### Building a New Service?
1. **[JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md#quick-start)** - Set up authentication (10 min)
2. **[RBAC-ABAC Quick Reference](./RBAC-ABAC-QUICK-REFERENCE.md#-5-minute-setup)** - Add authorization (5 min)
3. **[JWT Quick Reference](./JWT-AUTH-QUICK-REFERENCE.md#testing)** - Write tests (15 min)

### Debugging Issues?
1. **[JWT Troubleshooting](./JWT-AUTH-TROUBLESHOOTING.md)** - Authentication issues
2. **[RBAC-ABAC Developer Guide](./RBAC-ABAC-DEVELOPER-GUIDE.md#troubleshooting)** - Authorization issues
3. **Working Examples** - See how others did it

### Understanding the System?
1. **[RBAC-ABAC Architecture](./RBAC-ABAC-ARCHITECTURE.md)** - System design
2. **[Cross-Service Auth Analysis](../docs/CROSS-SERVICE-AUTH-ANALYSIS.md)** - Integration patterns
3. **[DRF Authentication Comparison](../docs/DRF-JWT-AUTHENTICATION-COMPARISON.md)** - Technical decisions

## 📁 Working Examples

Study these real implementations:

- **[billing-api](../billing-api/)** - Simple JWT authentication
- **[azure-costs](../azure-costs/)** - Full RBAC-ABAC integration
- **[cielo-website](../cielo-website/)** - Authentication provider
- **[identity-provider](../identity-provider/)** - Core identity service

## 🔑 Key Concepts

### Authentication & Authorization Flow
```
┌─────────┐      ┌──────────┐      ┌──────────────┐      ┌────────────┐
│  User   │─────▶│  CIELO   │─────▶│   Your API   │─────▶│   Redis    │
│         │ Login│ Website  │ JWT  │  Service     │ Attrs│   Cache    │
└─────────┘      └──────────┘      └──────────────┘      └────────────┘
                                           │
                                           ▼
                                    ┌──────────────┐
                                    │ Policy Engine│
                                    │   (ABAC)     │
                                    └──────────────┘
```

### Core Principles

1. **Separation of Concerns**
   - JWT handles authentication (who you are)
   - RBAC handles roles (what groups you're in)
   - ABAC handles permissions (what you can do)

2. **Service Autonomy**
   - Each service declares its own roles
   - Services manage their own policies
   - No central permission database

3. **Performance First**
   - Redis caching for user attributes
   - Database filtering when possible
   - Fail fast on permission checks

## ✅ Best Practices

### DO:
- Use `@permission_classes([IsAuthenticated])` for basic auth
- Define service manifests for roles/attributes
- Cache user attributes in Redis
- Write comprehensive tests
- Follow existing patterns

### DON'T:
- Configure REST_FRAMEWORK authentication_classes
- Implement custom authentication logic
- Store permissions in JWT tokens
- Skip service registration
- Ignore performance implications

## 🛠️ Development Workflow

### 1. Plan Your Service
- Define roles needed
- Identify user attributes
- Plan authorization policies
- Design API endpoints

### 2. Implement Authentication
```python
# 1. Add JWT middleware
MIDDLEWARE = [
    'common.jwt_auth.middleware.JWTAuthenticationMiddleware',
    ...
]

# 2. Protect endpoints
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_view(request):
    return Response({"user": request.user.username})
```

### 3. Add Authorization
```python
# 1. Create manifest
SERVICE_MANIFEST = {
    "service": {"name": "myservice"},
    "roles": [{"name": "admin"}],
    "attributes": [{"name": "department"}]
}

# 2. Define policies
@register_policy('department_match')
def department_match(user_attrs, obj=None, action=None):
    return user_attrs.department == obj.department

# 3. Apply to models
class MyModel(ABACModelMixin, models.Model):
    ABAC_POLICIES = {'view': 'department_match'}
```

### 4. Test Everything
```python
# Test authentication
response = client.get('/api/private/')
assert response.status_code == 401

# Test authorization
user_attrs = UserAttributes(department='Engineering')
assert my_policy(user_attrs, obj) == True
```

## 🔗 Related Documentation

### System Documentation
- [RBAC-ABAC Implementation](../docs/RBAC-ABAC-IMPLEMENTATION.md)
- [Cross-Service Auth Analysis](../docs/CROSS-SERVICE-AUTH-ANALYSIS.md)
- [Azure Costs Migration Summary](../docs/AZURE-COSTS-MIGRATION-SUMMARY.md)

### Service-Specific Docs
- [Identity Provider Logging](../identity-provider/docs/Logging.md)
- [Billing API Logging](../billing-api/docs/Logging.md)
- [CIELO Website Logging](../cielo_website/docs/Logging.md)

## 🤝 Contributing

When adding features or fixing issues:

1. **Update Documentation**
   - Keep guides current with changes
   - Add new patterns to quick references
   - Document architectural decisions

2. **Add Examples**
   - Show real implementations
   - Include test cases
   - Demonstrate edge cases

3. **Test Thoroughly**
   - Unit tests for policies
   - Integration tests for flows
   - Performance tests for scale

4. **Consider Security**
   - Follow secure defaults
   - Document security implications
   - Review with security mindset

## 📞 Support

- **Quick questions:** Check quick references first
- **Debugging:** Use troubleshooting guides
- **Architecture:** Review design documents
- **Examples:** Study working implementations

Remember: Good documentation saves everyone time!