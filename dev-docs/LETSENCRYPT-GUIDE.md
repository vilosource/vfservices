# Let's Encrypt SSL Certificate Guide

## Overview

This project uses Let's Encrypt to provide free SSL certificates for all services. We use the DNS-01 challenge method via Cloudflare DNS, which allows us to obtain wildcard certificates without exposing port 80/443 during the validation process.

## Certificate Coverage

The project obtains certificates for the following domains:
- `vfservices.viloforge.com` (base domain)
- `*.vfservices.viloforge.com` (wildcard for all subdomains)
- `cielo.viloforge.com` (CIELO website domain)
- `*.cielo.viloforge.com` (wildcard for CIELO subdomains)
- `maltacentral.com` (Malta Central website domain)
- `www.maltacentral.com` (Malta Central www subdomain)

## Prerequisites

1. **Cloudflare Account**: Your domains must use Cloudflare DNS
2. **Cloudflare API Token**: Create a token with DNS edit permissions
3. **Email Address**: Required for Let's Encrypt registration

### Creating a Cloudflare API Token

1. Log into Cloudflare Dashboard
2. Go to "My Profile" → "API Tokens"
3. Click "Create Token"
4. Use template "Edit zone DNS" or create custom token with:
   - Permissions: `Zone:DNS:Edit`
   - Zone Resources: Include your domain zones
5. Save the token securely

## Certificate Management

### Initial Certificate Generation

```bash
# Set required environment variables
export CLOUDFLARE_API_TOKEN="your-cloudflare-api-token"
export LETSENCRYPT_EMAIL="your-email@example.com"
export BASE_DOMAIN="vfservices.viloforge.com"  # or your custom domain

# Generate certificates
make certbot-renew
```

### Certificate Renewal

Let's Encrypt certificates are valid for 90 days. The `certbot-renew` target forces renewal:

```bash
# Force renewal (even if not due)
make certbot-renew
```

For automatic renewal, consider setting up a cron job:
```bash
# Add to crontab (runs weekly on Sunday at 2 AM)
0 2 * * 0 cd /path/to/vfservices && CLOUDFLARE_API_TOKEN=xxx LETSENCRYPT_EMAIL=xxx make certbot-renew
```

### Quick Certificate Setup

For development or when Let's Encrypt isn't available:
```bash
# Generate self-signed certificates
make generate-self-signed-cert
```

## Certificate Storage

Certificates are stored in the `./certs/` directory:
```
certs/
└── live/
    └── vfservices.viloforge.com/
        ├── cert.pem       # Certificate only
        ├── chain.pem      # Intermediate certificates
        ├── fullchain.pem  # Certificate + intermediates (use this)
        └── privkey.pem    # Private key (use this)
```

## Integration with Services

### Docker Services
Services in `docker-compose.yml` mount the certificate directory:
```yaml
volumes:
  - ./certs:/certs:ro
```

### Traefik Configuration
Traefik uses the certificates for HTTPS termination:
```yaml
environment:
  - TRAEFIK_PROVIDERS_FILE_FILENAME=/certs/live/${BASE_DOMAIN}/fullchain.pem
  - TRAEFIK_PROVIDERS_FILE_KEY=/certs/live/${BASE_DOMAIN}/privkey.pem
```

### Django Development
For local development with `runserver_plus`:
```bash
make up  # Automatically uses certificates from certs directory
```

## How It Works

1. **DNS Challenge**: Certbot creates a TXT record in your Cloudflare DNS
2. **Validation**: Let's Encrypt validates you control the domain
3. **Certificate Issuance**: Certificates are generated and saved locally
4. **Cleanup**: The temporary DNS record is removed

The DNS challenge allows obtaining certificates without:
- Opening firewall ports
- Running a web server
- Affecting production traffic

## Troubleshooting

### Common Issues

1. **Invalid API Token**
   ```
   Error: Invalid Cloudflare credentials
   ```
   Solution: Verify your API token has DNS edit permissions

2. **Rate Limits**
   ```
   Error: Too many certificates already issued
   ```
   Solution: Let's Encrypt has rate limits. Wait or use staging environment

3. **DNS Propagation**
   ```
   Error: DNS problem: NXDOMAIN
   ```
   Solution: Ensure domain exists and DNS has propagated

### Testing Certificate Setup

```bash
# Check certificate details
openssl x509 -in certs/live/vfservices.viloforge.com/cert.pem -text -noout

# Verify certificate chain
openssl verify -CAfile certs/live/vfservices.viloforge.com/chain.pem \
  certs/live/vfservices.viloforge.com/cert.pem

# Test HTTPS connection
curl -v https://vfservices.viloforge.com
```

## Security Best Practices

1. **Protect API Token**: Never commit the Cloudflare API token to git
2. **Secure Storage**: Ensure `certs/` directory has appropriate permissions
3. **Regular Renewal**: Set up automated renewal before expiration
4. **Monitor Expiration**: Set up alerts for certificate expiration

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `CLOUDFLARE_API_TOKEN` | API token with DNS edit permissions | `abc123...` |
| `LETSENCRYPT_EMAIL` | Email for Let's Encrypt notifications | `admin@example.com` |
| `BASE_DOMAIN` | Primary domain for services | `vfservices.viloforge.com` |

## Related Files

- `/scripts/renew_all_certs.sh` - Certificate renewal script
- `/scripts/generate_certs.sh` - Self-signed certificate generator
- `Makefile` - Contains `cert` and `certbot-renew` targets
- `docker-compose.yml` - Service configuration with certificate mounts

## Quick Reference

```bash
# Get/renew certificates
make certbot-renew

# Use wrapper script
make cert

# Generate self-signed (development)
make generate-self-signed-cert

# Start services with HTTPS
make docker-https
```

## Current Certificate Status

As of 2025-01-22, the project has a valid Let's Encrypt certificate covering all domains:
- Certificate expiration: 2025-09-20
- Domains covered: vfservices.viloforge.com, *.vfservices.viloforge.com, cielo.viloforge.com, *.cielo.viloforge.com, maltacentral.com, www.maltacentral.com

## Changelog

- 2025-01-22T15:50:00Z: Successfully renewed certificates including maltacentral.com domains
- 2025-01-22T10:45:00Z: Added maltacentral.com and www.maltacentral.com to certificate coverage
- 2025-01-22: Initial documentation created

---

*Last updated: 2025-01-22*