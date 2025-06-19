# Domain Configuration Guide

## Overview

The VF Services platform supports configurable domain names through the `BASE_DOMAIN` environment variable. This allows the entire platform to be deployed on different domains without modifying any source code.

## How It Works

### Environment Variable

The platform uses a single `BASE_DOMAIN` environment variable that controls all service domains:

```bash
# Default domain
BASE_DOMAIN=vfservices.viloforge.com

# Custom domain examples
BASE_DOMAIN=mycompany.com
BASE_DOMAIN=staging.example.com
BASE_DOMAIN=local.test
```

### Service Subdomains

Each service automatically uses a subdomain of the BASE_DOMAIN:

| Service | URL Pattern | Example (BASE_DOMAIN=example.com) |
|---------|-------------|-----------------------------------|
| Website | `https://{BASE_DOMAIN}` or `https://website.{BASE_DOMAIN}` | `https://example.com` or `https://website.example.com` |
| Identity Provider | `https://identity.{BASE_DOMAIN}` | `https://identity.example.com` |
| Billing API | `https://billing.{BASE_DOMAIN}` | `https://billing.example.com` |
| Inventory API | `https://inventory.{BASE_DOMAIN}` | `https://inventory.example.com` |

## Configuration Locations

### 1. Docker Compose

The `docker-compose.yml` file propagates BASE_DOMAIN to all services:

```yaml
environment:
  - BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
  - SSO_COOKIE_DOMAIN=.${BASE_DOMAIN:-vfservices.viloforge.com}
```

Traefik routing rules also use the variable:

```yaml
labels:
  - "traefik.http.routers.website.rule=Host(\`website.${BASE_DOMAIN:-vfservices.viloforge.com}\`) || Host(\`${BASE_DOMAIN:-vfservices.viloforge.com}\`)"
```

### 2. Django Settings

Each Django service reads BASE_DOMAIN from the environment:

```python
# Base domain configuration
BASE_DOMAIN = os.environ.get("BASE_DOMAIN", "vfservices.viloforge.com")

# Dynamic ALLOWED_HOSTS
ALLOWED_HOSTS = [
    f"billing.{BASE_DOMAIN}",
    f".{BASE_DOMAIN}",
    "localhost",
    "127.0.0.1",
    "billing-api"
]

# Dynamic CORS configuration
CORS_ALLOWED_ORIGINS = [
    f"https://website.{BASE_DOMAIN}",
    f"https://{BASE_DOMAIN}",
    "http://localhost:8080",
]
```

### 3. Templates

Website templates use a context processor to access service URLs:

```django
<!-- In templates -->
<a href="{{ SERVICE_URLS.identity }}">Identity Provider</a>
<a href="{{ SERVICE_URLS.billing }}">Billing API</a>
```

The context processor (`website/webapp/context_processors.py`) provides:

```python
{
    'SERVICE_URLS': {
        'identity': 'https://identity.example.com',
        'website': 'https://website.example.com',
        'billing': 'https://billing.example.com',
        'inventory': 'https://inventory.example.com',
    },
    'BASE_DOMAIN': 'example.com'
}
```

### 4. Test Configuration

Tests can be configured for different domains using the template:

```bash
# Generate test configuration
./scripts/generate_test_env.sh mytest.local

# Or set BASE_DOMAIN and generate
export BASE_DOMAIN=staging.example.com
./scripts/generate_test_env.sh
```

## Deployment Guide

### 1. Set the Domain

Create a `.env` file in the project root:

```bash
BASE_DOMAIN=mycompany.com
```

Or export it:

```bash
export BASE_DOMAIN=mycompany.com
```

### 2. SSL Certificates

Generate or obtain SSL certificates for your domain:

```bash
# For self-signed certificates
./scripts/generate_certs.sh

# For production (Let's Encrypt)
./scripts/run_certbot.sh
```

Certificates should be placed in:
- `/certs/live/{BASE_DOMAIN}/fullchain.pem`
- `/certs/live/{BASE_DOMAIN}/privkey.pem`

### 3. Start Services

```bash
docker-compose up -d
```

All services will automatically use the configured domain.

### 4. Verify Configuration

Check that services are accessible:

```bash
# Check main website
curl https://mycompany.com

# Check identity service
curl https://identity.mycompany.com/api/

# Check other services
curl https://billing.mycompany.com/api/
curl https://inventory.mycompany.com/api/
```

## Testing with Different Domains

### Local Development

For local development, you can use a test domain:

1. Add entries to `/etc/hosts`:
   ```
   127.0.0.1 local.test
   127.0.0.1 identity.local.test
   127.0.0.1 website.local.test
   127.0.0.1 billing.local.test
   127.0.0.1 inventory.local.test
   ```

2. Set BASE_DOMAIN:
   ```bash
   export BASE_DOMAIN=local.test
   ```

3. Generate self-signed certificates:
   ```bash
   ./scripts/generate_certs.sh
   ```

4. Start services:
   ```bash
   docker-compose up
   ```

### Staging Environment

For staging deployments:

```bash
# Set staging domain
export BASE_DOMAIN=staging.mycompany.com

# Deploy
docker-compose up -d
```

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure all Django services have restarted with the new BASE_DOMAIN
2. **SSL Certificate Errors**: Verify certificates match the configured domain
3. **Cookie Issues**: Clear browser cookies when switching domains
4. **DNS Resolution**: Ensure DNS records exist for all subdomains

### Verification Commands

```bash
# Check environment variables in a container
docker-compose exec website env | grep BASE_DOMAIN

# Check Django settings
docker-compose exec website python manage.py shell
>>> from django.conf import settings
>>> print(settings.BASE_DOMAIN)
>>> print(settings.ALLOWED_HOSTS)

# Check Traefik routing
docker-compose logs traefik | grep -i host
```

## Security Considerations

1. **ALLOWED_HOSTS**: Django services automatically configure ALLOWED_HOSTS based on BASE_DOMAIN
2. **CORS Origins**: CORS is configured to allow requests between services on the same BASE_DOMAIN
3. **SSL/TLS**: Always use valid SSL certificates for production domains
4. **Cookie Domain**: SSO cookies are scoped to the BASE_DOMAIN for security

## Migration Guide

To migrate an existing deployment to a new domain:

1. **Backup** all data
2. **Update DNS** records for the new domain
3. **Obtain SSL certificates** for the new domain
4. **Set BASE_DOMAIN** to the new value
5. **Restart all services**: `docker-compose down && docker-compose up -d`
6. **Update external integrations** (webhooks, OAuth callbacks, etc.)
7. **Test thoroughly** before switching production traffic

## Best Practices

1. **Use Environment Files**: Store BASE_DOMAIN in `.env` files for different environments
2. **Automate Certificate Management**: Use Let's Encrypt with automatic renewal
3. **Test Domain Changes**: Always test domain changes in a staging environment first
4. **Monitor After Changes**: Watch logs and monitoring after domain changes
5. **Document Custom Domains**: Keep a record of all domains used in different environments

## Example Configurations

### Production
```bash
# .env.production
BASE_DOMAIN=vfservices.com
```

### Staging
```bash
# .env.staging
BASE_DOMAIN=staging.vfservices.com
```

### Development
```bash
# .env.development
BASE_DOMAIN=dev.local
```

### Multi-tenant
```bash
# Customer A
BASE_DOMAIN=vf.customera.com

# Customer B
BASE_DOMAIN=vf.customerb.com
```

## Summary

The domain configuration system provides:

- **Single configuration point**: One environment variable controls all domains
- **No code changes**: Deploy to any domain without modifying source code
- **Automatic service discovery**: Services automatically find each other using BASE_DOMAIN
- **Flexible deployment**: Support for local, staging, and production environments
- **Multi-tenant ready**: Deploy multiple instances on different domains