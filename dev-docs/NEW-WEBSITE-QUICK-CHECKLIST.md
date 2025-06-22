# Quick Checklist: New Website Setup

Use this checklist when setting up a new website on VF Services platform. Check off each item as you complete it.

## Pre-Setup
- [ ] Domain name decided
- [ ] SSL certificate includes your domain (or ready to add it)
- [ ] Have access to VF Services repository

## Setup Steps

### 1. Copy Project Files
- [ ] `cp -r website your-website-name`
- [ ] `cp website/Dockerfile your-website-name/Dockerfile`

### 2. Docker Compose Configuration
- [ ] Add new service to docker-compose.yml
- [ ] Set `SSO_COOKIE_DOMAIN=.yourdomain.com`
- [ ] Set `APPLICATION_SET_DOMAIN=yourdomain.com`
- [ ] Set unique database name `POSTGRES_DB=vfdb_yourwebsite`
- [ ] Configure Traefik labels with your domain

### 3. Identity Provider
- [ ] Add your domain to identity-provider's ALLOWED_APPLICATION_DOMAINS
- [ ] Example: `ALLOWED_APPLICATION_DOMAINS=vfservices.viloforge.com,cielo.viloforge.com,yourdomain.com`

### 4. CRITICAL BUG FIX
- [ ] **Fix login form field name** in `accounts/templates/accounts/login.html`
  - Change: `name="username"` 
  - To: `name="email"`
  - Also update: `id="email"` and `value="{{ request.POST.email|default:'' }}"`

### 5. SSL Certificate
- [ ] Verify certificate includes your domain:
  ```bash
  docker compose exec traefik cat /etc/certs/live/vfservices.viloforge.com/cert.pem | \
    openssl x509 -text -noout | grep DNS
  ```

### 6. Start Services
- [ ] `docker compose up -d postgres redis identity-provider your-website-name traefik`
- [ ] Check all services running: `docker compose ps`

### 7. Create/Verify Admin User
- [ ] Check if admin exists in identity-provider
- [ ] Create if needed (username: admin, password: admin123)

### 8. Test Login
- [ ] Access: https://www.yourdomain.com/accounts/login/
- [ ] Login with admin/admin123
- [ ] Verify redirect to home page
- [ ] Check browser cookies for JWT token

### 9. Verify Logs
- [ ] No errors in: `docker compose logs your-website-name`
- [ ] Authentication successful in logs
- [ ] User role recognized

## Common Gotchas
- [ ] Form field MUST be `name="email"` not `name="username"`
- [ ] Domain MUST be in identity-provider's allowed list
- [ ] Cookie domain MUST match your domain
- [ ] Each website needs unique database name
- [ ] Admin user is shared across all services

## Quick Debug Commands
```bash
# Check logs
docker compose logs your-website-name --tail 50

# Test identity provider
curl -X POST http://localhost:8100/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Restart service
docker compose restart your-website-name
```

## Success Indicators
- [ ] Login page loads without errors
- [ ] Form submission triggers POST request
- [ ] Logs show "Authentication successful"
- [ ] User redirected after login
- [ ] Home page shows authenticated user

---
Print this checklist and check off items as you complete them!