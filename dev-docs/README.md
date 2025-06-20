# VF Services Developer Documentation

## JWT Authentication Documentation

Complete guides for implementing JWT authentication in new API services.

### 📚 Documentation Index

| Document | Purpose | Audience |
|----------|---------|----------|
| **[JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)** | Complete implementation guide | New service developers |
| **[Quick Reference](./JWT-AUTH-QUICK-REFERENCE.md)** | Copy-paste patterns and examples | Experienced developers |
| **[Troubleshooting Guide](./JWT-AUTH-TROUBLESHOOTING.md)** | Common issues and solutions | All developers |

### 🚀 Quick Start

1. **New to JWT auth?** → Start with [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
2. **Need quick patterns?** → Use [Quick Reference](./JWT-AUTH-QUICK-REFERENCE.md)  
3. **Having issues?** → Check [Troubleshooting Guide](./JWT-AUTH-TROUBLESHOOTING.md)

### 📁 Working Examples

- **[billing-api](../billing-api/)** - Simple, working JWT authentication
- **[azure-costs](../azure-costs/)** - Full RBAC integration example
- **[cielo-website](../cielo-website/)** - Authentication provider example

### 🔗 Related Documentation

- [RBAC-ABAC Implementation](../docs/RBAC-ABAC-IMPLEMENTATION.md)
- [Cross-Service Auth Analysis](../docs/CROSS-SERVICE-AUTH-ANALYSIS.md)
- [DRF Authentication Comparison](../docs/DRF-JWT-AUTHENTICATION-COMPARISON.md)

## Key Concepts

### Authentication Flow
```
User → CIELO Login → JWT Cookie → Your API → Middleware → DRF → Response
```

### Core Principle
> **Use JWT middleware for authentication, DRF for authorization**
> 
> The shared JWT middleware handles token validation and user creation. Your service just uses standard DRF patterns like `@permission_classes([IsAuthenticated])`.

### Best Practices

✅ **DO:**
- Use `@permission_classes([IsAuthenticated])` for protected endpoints
- Let JWT middleware handle authentication automatically
- Check roles via `request.user_attrs.roles`
- Follow the working examples (billing-api, azure-costs)

❌ **DON'T:**
- Configure REST_FRAMEWORK authentication classes
- Do manual authentication checks in views
- Override middleware authentication in DRF
- Reinvent the authentication wheel

## Development Workflow

1. **Plan your service**
   - Define required roles and permissions
   - Plan your API endpoints

2. **Follow the guide**
   - Use [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
   - Copy patterns from [Quick Reference](./JWT-AUTH-QUICK-REFERENCE.md)

3. **Test thoroughly**
   - Create Playwright integration tests
   - Test cross-service authentication
   - Verify role-based access control

4. **Deploy and monitor**
   - Use provided deployment checklist
   - Monitor authentication logs
   - Watch for security issues

## Contributing

When adding new authentication features or fixing issues:

1. **Update documentation** - Keep these guides current
2. **Add troubleshooting** - Document new issues and solutions  
3. **Update examples** - Ensure working examples stay working
4. **Test across services** - Verify changes don't break existing services

## Support

- **Documentation issues:** Update the relevant guide
- **Authentication bugs:** Check [Troubleshooting Guide](./JWT-AUTH-TROUBLESHOOTING.md) first
- **New features:** Follow established patterns and update documentation