# New Website Setup Guide for VF Services Platform

## Overview
This guide provides step-by-step instructions for setting up a new website on the VF Services platform. It consolidates all learnings from the maltacentral-web setup and provides a checklist to ensure nothing is missed.

## Prerequisites
- Docker and Docker Compose installed
- Access to the VF Services repository
- SSL certificate that includes your domain (or ability to generate one)
- Basic understanding of Django and Docker

## Step-by-Step Setup Process

### Step 1: Copy Base Website Project
```bash
# Copy the existing website project as your starting point
cp -r website your-website-name

# Copy the Dockerfile
cp website/Dockerfile your-website-name/Dockerfile
```

### Step 2: Add Service to docker-compose.yml
Add your new service to `docker-compose.yml`. Here's the template:

```yaml
  your-website-name:
    build:
      context: .
      dockerfile: your-website-name/Dockerfile
    working_dir: /code/your-website-name
    volumes:
      - ./your-website-name:/code/your-website-name
      - ./common:/code/common
    environment:
      - PYTHONPATH=/code
      - VF_JWT_SECRET=${VF_JWT_SECRET:-change-me}
      - SSO_COOKIE_DOMAIN=.yourdomain.com  # Important: Your domain
      - APPLICATION_SET_DOMAIN=yourdomain.com  # Important: Your domain
      - POSTGRES_HOST=postgres
      - POSTGRES_DB=vfdb_yourwebsite  # Unique database name
      - POSTGRES_USER=${POSTGRES_USER:-vfuser}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-vfpass}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - RBAC_ABAC_CACHE_TTL=${RBAC_ABAC_CACHE_TTL:-86400}
      - IDENTITY_PROVIDER_URL=http://identity-provider:8000
      - IDENTITY_EXTERNAL_URL=https://identity.vfservices.viloforge.com  # Important: Shared identity provider
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.yourwebsite.rule=Host(`www.yourdomain.com`) || Host(`yourdomain.com`)"
      - "traefik.http.routers.yourwebsite.entrypoints=websecure"
      - "traefik.http.routers.yourwebsite.tls=true"
      - "traefik.http.services.yourwebsite.loadbalancer.server.port=8000"
      - "traefik.http.services.yourwebsite.loadbalancer.passHostHeader=true"
```

### Step 3: Update Identity Provider Allowed Domains
In `docker-compose.yml`, find the identity-provider service and add your domain to ALLOWED_APPLICATION_DOMAINS:

```yaml
  identity-provider:
    environment:
      - ALLOWED_APPLICATION_DOMAINS=vfservices.viloforge.com,cielo.viloforge.com,yourdomain.com
```

### Step 4: SSL Certificate Configuration

#### Option A: Add to Existing Certificate
If using Let's Encrypt, add your domain to the certificate generation:
```bash
# Update the certificate to include your domain
CLOUDFLARE_API_TOKEN=your_token LETSENCRYPT_EMAIL=your@email.com make certbot-renew
```

#### Option B: Use Existing Certificate
Ensure your domain is included in the certificate at:
- Certificate: `/certs/live/vfservices.viloforge.com/fullchain.pem`
- Key: `/certs/live/vfservices.viloforge.com/privkey.pem`

Verify domains in certificate:
```bash
docker compose exec traefik cat /etc/certs/live/vfservices.viloforge.com/cert.pem | openssl x509 -text -noout | grep -A2 "Subject Alternative Name"
```

### Step 5: Critical Bug Fixes

#### Fix 1: Login Form Field Name (CRITICAL!)
The login form has a field name mismatch that prevents login. Fix it:

**File**: `your-website-name/accounts/templates/accounts/login.html`

Find:
```html
<input class="form-control" type="text" id="username" name="username" required 
       placeholder="Enter your username or email" value="{{ request.POST.username|default:'' }}">
```

Replace with:
```html
<input class="form-control" type="text" id="email" name="email" required 
       placeholder="Enter your username or email" value="{{ request.POST.email|default:'' }}">
```

**Why**: The Django view expects `request.POST.get("email")` but the form sends `name="username"`.

#### Fix 2: HEAD Request Support (Optional)
The login view doesn't handle HEAD requests properly. To fix monitoring/health checks:

**File**: `your-website-name/accounts/views.py`

Add HEAD support:
```python
if request.method in ["GET", "HEAD"]:
    # existing GET logic
```

### Step 6: Database Configuration
Each website needs its own database. The database name is set in the environment variable `POSTGRES_DB`.

Convention: `vfdb_yourwebsite`

The database will be created automatically when the service starts.

### Step 7: Start and Test Services

1. **Start required services:**
   ```bash
   docker compose up -d postgres redis identity-provider your-website-name traefik
   ```

2. **Check service status:**
   ```bash
   docker compose ps | grep -E "(your-website-name|identity-provider|traefik)"
   ```

3. **Monitor logs:**
   ```bash
   docker compose logs your-website-name -f
   ```

### Step 8: Create Admin User (First Time Only)
The admin user is shared across all services via identity-provider:

```bash
docker compose exec identity-provider python manage.py shell
```

```python
from identity_app.models import User
from django.contrib.auth.hashers import make_password

if not User.objects.filter(username='admin').exists():
    User.objects.create(
        username='admin',
        email='admin@yourdomain.com',
        password=make_password('admin123'),
        is_active=True,
        is_admin=True
    )
    print("Admin user created")
```

### Step 9: Test Login
1. Navigate to: `https://www.yourdomain.com/accounts/login/`
2. Login with:
   - Username: `admin` (NOT email, even though field says "Email")
   - Password: `admin123`

### Step 10: Verify Authentication Flow

Check logs for successful authentication:
```bash
docker compose logs your-website-name | grep -E "(Login successful|Authentication successful)"
docker compose logs identity-provider | grep -E "(API authentication successful)"
```

## Common Issues and Solutions

### Issue 1: Login Form Not Submitting
**Symptom**: Click login but nothing happens
**Cause**: Form field name mismatch
**Solution**: Ensure form field is `name="email"` not `name="username"`

### Issue 2: 500 Error on Login Page
**Symptom**: Error when accessing login page
**Cause**: HEAD request not handled
**Solution**: Optional - add HEAD support to login view

### Issue 3: Authentication Fails
**Symptom**: Invalid credentials error
**Possible Causes**:
1. Admin user doesn't exist - create it
2. Wrong password - default is `admin123`
3. Domain not in ALLOWED_APPLICATION_DOMAINS - add it

### Issue 4: Page Not Loading
**Symptom**: Connection refused or timeout
**Check**:
1. Service is running: `docker compose ps`
2. SSL certificate includes your domain
3. Traefik labels are correct in docker-compose.yml

### Issue 5: Profile Page API Errors
**Symptom**: JavaScript error "Failed to load resource: net::ERR_NAME_NOT_RESOLVED"
**Cause**: Profile page trying to access identity.yourdomain.com instead of shared identity provider
**Solution**: Add `IDENTITY_EXTERNAL_URL=https://identity.vfservices.viloforge.com` to environment variables

## Important Configuration Notes

### Cookie Domains
- Each base domain has separate authentication
- Users must login separately for each domain
- SSO works within subdomains of the same base domain

### Environment Variables
Key variables to customize:
- `SSO_COOKIE_DOMAIN`: Must be `.yourdomain.com`
- `APPLICATION_SET_DOMAIN`: Must be `yourdomain.com`
- `POSTGRES_DB`: Must be unique (e.g., `vfdb_yourwebsite`)

### Django Settings
The settings.py uses environment variables, so no code changes needed:
```python
APPLICATION_SET_DOMAIN = os.environ.get("APPLICATION_SET_DOMAIN", "yourdomain.com")
SSO_COOKIE_DOMAIN = os.environ.get("SSO_COOKIE_DOMAIN", ".yourdomain.com")
```

## Testing Checklist

- [ ] Service starts without errors
- [ ] Login page loads at https://www.yourdomain.com/accounts/login/
- [ ] Form submission works (check browser network tab)
- [ ] Authentication succeeds (check logs)
- [ ] User redirected to home page after login
- [ ] JWT cookies set with correct domain
- [ ] Protected pages accessible after login
- [ ] Logout works correctly

## File Structure
After setup, your website directory should contain:
```
your-website-name/
├── Dockerfile
├── accounts/
│   ├── templates/
│   │   └── accounts/
│   │       └── login.html  # Check field name!
│   └── views.py
├── main/
│   └── settings.py
├── static/
├── templates/
└── webapp/
```

## Security Considerations

1. **Change default passwords** in production
2. **Use strong JWT secrets** - update VF_JWT_SECRET
3. **Enable HTTPS only** - Traefik handles this
4. **Restrict ALLOWED_HOSTS** in production
5. **Regular certificate renewal** - automate with cron

## Troubleshooting Commands

```bash
# Check if services are running
docker compose ps

# View real-time logs
docker compose logs -f your-website-name

# Test identity provider directly
curl -X POST http://localhost:8100/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Check SSL certificate domains
docker compose exec traefik cat /etc/certs/live/vfservices.viloforge.com/cert.pem | \
  openssl x509 -text -noout | grep DNS

# Access Django shell
docker compose exec your-website-name python manage.py shell

# Check Redis connectivity
docker compose exec your-website-name python -c "from common.rbac_abac.redis_client import get_redis_client; print(get_redis_client().ping())"
```

## Next Steps

1. Customize the website appearance and functionality
2. Add specific business logic for your use case
3. Configure proper logging and monitoring
4. Set up automated backups for the database
5. Implement CI/CD pipeline for deployments

## References

- [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
- [RBAC/ABAC Architecture](./RBAC-ABAC-ARCHITECTURE.md)
- [Malta Central Setup Diary](./MALTACENTRAL-WEB-SETUP-STEPS.md)

---

Last Updated: 2025-01-22
Based on: maltacentral-web implementation