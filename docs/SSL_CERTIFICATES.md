# SSL Certificate Configuration for VF Services

## Overview

VF Services uses Let's Encrypt certificates obtained via Cloudflare DNS validation for all HTTPS traffic. The project supports multiple domains:

- `vfservices.viloforge.com` (main domain)
- `*.vfservices.viloforge.com` (all subdomains)
- `cielo.viloforge.com` (CIELO application domain)
- `*.cielo.viloforge.com` (all CIELO subdomains)

## Certificate Management

### Prerequisites

1. **Cloudflare API Token**: You need a Cloudflare API token with DNS edit permissions for the domains.
2. **Email Address**: Required for Let's Encrypt notifications.

### Environment Variables

Set these before running certificate commands:

```bash
export CLOUDFLARE_API_TOKEN=your-cloudflare-api-token
export LETSENCRYPT_EMAIL=your-email@example.com
```

### Obtaining/Renewing Certificates

To obtain or renew certificates for all domains:

```bash
make cert
```

This command will:
1. Use Cloudflare DNS validation
2. Obtain a single certificate covering all domains
3. Store the certificate in `./certs/live/vfservices.viloforge.com/`

### Force Renewal

To force renewal of existing certificates:

```bash
make certbot-renew
```

## Certificate Coverage

The certificate includes:
- `vfservices.viloforge.com`
- `*.vfservices.viloforge.com` (covers identity, website, billing, inventory subdomains)
- `cielo.viloforge.com`
- `*.cielo.viloforge.com`

### Verifying Certificate Coverage

To check which domains are covered by the current certificate:

```bash
openssl x509 -in ./certs/live/vfservices.viloforge.com/cert.pem -text -noout | grep -A2 "Subject Alternative Name"
```

## Traefik Configuration

Traefik automatically uses the certificate for all configured routes. The certificate is mounted at:
- Certificate: `/etc/certs/live/vfservices.viloforge.com/fullchain.pem`
- Private Key: `/etc/certs/live/vfservices.viloforge.com/privkey.pem`

The configuration is in `traefik/dynamic/tls-config.yaml`.

## Testing SSL Certificates

### Using Playwright Tests

The Playwright tests include SSL certificate validation:

```bash
# Run all Cielo website tests including SSL validation
cd playwright/cielo-website/smoke-tests
pytest test_cielo_index.py::test_cielo_ssl_certificate -v

# Run all VF Services website tests including SSL validation
cd playwright/website/smoke-tests
pytest test_vfservices_access.py::test_vfservices_ssl_certificate -v
```

### Manual Testing

Test SSL certificate validity:

```bash
# Test vfservices.viloforge.com
openssl s_client -connect vfservices.viloforge.com:443 -servername vfservices.viloforge.com

# Test cielo.viloforge.com
openssl s_client -connect cielo.viloforge.com:443 -servername cielo.viloforge.com
```

## Troubleshooting

### Certificate Not Covering Expected Domains

If you see errors about certificates not covering certain domains:

1. Check current certificate coverage:
   ```bash
   openssl x509 -in ./certs/live/vfservices.viloforge.com/cert.pem -text -noout | grep DNS
   ```

2. Renew certificate with all domains:
   ```bash
   make cert
   ```

3. Restart services:
   ```bash
   docker-compose restart traefik
   ```

### Self-Signed Certificate Warnings

In development, you might see self-signed certificate warnings. This is normal if you haven't obtained Let's Encrypt certificates yet.

For production, always use valid Let's Encrypt certificates by running `make cert` with proper Cloudflare credentials.

### DNS Validation Failures

If certificate generation fails:

1. Verify Cloudflare API token has correct permissions
2. Ensure DNS records exist for all requested domains
3. Wait for DNS propagation (60 seconds is configured)
4. Check Cloudflare DNS records are properly configured

## Adding New Domains

To add new domains to the certificate:

1. Update `scripts/renew_all_certs.sh` to include new domains
2. Update `Makefile` certbot-renew target
3. Run `make cert` to obtain updated certificate
4. Update Traefik labels in `docker-compose.yml` for new services