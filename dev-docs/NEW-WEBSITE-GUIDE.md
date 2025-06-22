# Malta Central Website Setup Guide

## Overview
This guide documents the process of creating maltacentral-web, a new Django project based on the existing website project, configured to run on www.maltacentral.com.

## SSL Certificate Status
- **Certificate obtained**: 2025-01-22
- **Valid until**: 2025-09-20
- **Domains covered**: maltacentral.com, www.maltacentral.com
- **Certificate type**: Let's Encrypt (via Cloudflare DNS challenge)
- **Certificate location**: `./certs/live/vfservices.viloforge.com/`

## Changes Made

### 1. Project Directory Creation
- **Action**: Copied entire website directory to maltacentral-web
- **Command**: `cp -r website maltacentral-web`
- **Timestamp**: 2025-01-22T10:00:00Z

### 2. Dockerfile Copy
- **Action**: Copied Dockerfile from website to maltacentral-web
- **Command**: `cp website/Dockerfile maltacentral-web/Dockerfile`
- **Timestamp**: 2025-01-22T10:02:00Z

### 3. Docker Compose Configuration
- **File**: docker-compose.yml
- **Action**: Added maltacentral-web service configuration
- **Timestamp**: 2025-01-22T10:03:00Z
- **Details**: 
  - Based on website service configuration
  - Updated domain to www.maltacentral.com
  - Changed database to use separate DB (vfdb_maltacentral)
  - Updated APPLICATION_SET_DOMAIN to maltacentral.com
  - Added complete service definition with all environment variables

### 4. Identity Provider Configuration Update
- **File**: docker-compose.yml
- **Action**: Updated identity-provider ALLOWED_APPLICATION_DOMAINS
- **Timestamp**: 2025-01-22T10:05:00Z
- **Details**: Added maltacentral.com to the allowed domains list

## Completed Tasks
- ✅ Copied website directory to maltacentral-web
- ✅ Copied Dockerfile to maltacentral-web
- ✅ Updated docker-compose.yml with maltacentral-web service
- ✅ Configured Traefik labels for www.maltacentral.com
- ✅ Updated identity-provider to allow maltacentral.com domain

## Notes
- The maltacentral-web project is based on the website Django project
- Uses environment variables for domain configuration (no code changes needed)
- Configured to use separate PostgreSQL database (vfdb_maltacentral)
- SSO cookie domain set to .maltacentral.com for authentication
- Ready to be started with docker compose

## Authentication Setup for Admin Access

### Understanding the Authentication Flow
1. User logs in at `https://www.maltacentral.com/accounts/login/`
2. maltacentral-web sends credentials to identity-provider
3. identity-provider validates and returns JWT token
4. JWT cookie is set with domain `.maltacentral.com`

### Key Configuration Issues
The current setup has a domain mismatch:
- maltacentral-web sets cookies for `.maltacentral.com`
- But identity-provider is configured for `.viloforge.com` domains only

### Solution for Admin Login

To enable admin login to maltacentral-web, you need to:

1. **Start the services:**
   ```bash
   docker compose up -d postgres redis identity-provider maltacentral-web
   ```

2. **Create admin user in identity-provider (if not exists):**
   ```bash
   docker compose exec identity-provider python manage.py shell
   ```
   ```python
   from identity_app.models import User
   from django.contrib.auth.hashers import make_password
   
   # Check if admin exists
   if not User.objects.filter(username='admin').exists():
       User.objects.create(
           username='admin',
           email='admin@maltacentral.com',
           password=make_password('admin123'),
           is_active=True,
           is_admin=True
       )
       print("Admin user created")
   else:
       print("Admin user already exists")
   ```

3. **Access the login page:**
   Navigate to `https://www.maltacentral.com/accounts/login/`

4. **Login with credentials:**
   - Username: `admin`
   - Password: `admin123`

### Important Notes
- The identity-provider is shared across all services
- Each domain (viloforge.com, maltacentral.com) has separate cookie sessions
- Users need to login separately for each domain
- The admin user created in identity-provider works across all domains

## Configuration Details

### Environment Variables
- `APPLICATION_SET_DOMAIN`: maltacentral.com
- `SSO_COOKIE_DOMAIN`: .maltacentral.com
- `POSTGRES_DB`: vfdb_maltacentral

### Traefik Configuration
- Host rule: www.maltacentral.com and maltacentral.com
- HTTPS enabled with automatic redirect
- Service port: 8000
- SSL certificate: Uses shared Let's Encrypt certificate

## SSL/HTTPS Setup

The maltacentral-web service uses the shared Let's Encrypt certificate that includes maltacentral.com and www.maltacentral.com domains. The certificate is:
- Automatically mounted via Docker volumes
- Managed by Traefik for HTTPS termination
- Renewed using `make certbot-renew` command

### Certificate Renewal
To renew certificates (including maltacentral.com):
```bash
CLOUDFLARE_API_TOKEN=your_token LETSENCRYPT_EMAIL=your@email.com make certbot-renew
```

## Changelog
- 2025-01-22T15:55:00Z: Added SSL certificate information and status
- 2025-01-22T10:00:00Z: Initial guide created