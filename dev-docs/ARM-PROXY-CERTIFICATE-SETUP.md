# ARM Proxy Certificate Setup

## Overview

This document describes how to obtain SSL certificates for arm-proxy.maltacentral.com.

## Prerequisites

1. Ensure you have the following environment variables set:
   ```bash
   export CLOUDFLARE_API_TOKEN="your-cloudflare-api-token"
   export LETSENCRYPT_EMAIL="your-email@example.com"
   ```

2. Ensure DNS records exist for arm-proxy.maltacentral.com pointing to your server

## Steps to Obtain Certificate

1. **Run the certificate renewal command**:
   ```bash
   make certbot-renew
   ```
   
   Or use the script directly:
   ```bash
   ./scripts/renew_all_certs.sh
   ```

2. **Verify the certificate was obtained**:
   ```bash
   # Check certificate domains
   openssl x509 -in ./certs/live/vfservices.viloforge.com/cert.pem -text -noout | grep -A2 'Subject Alternative Name'
   ```

3. **Restart Traefik to use the new certificate**:
   ```bash
   docker compose restart traefik
   ```

4. **Test the SSL certificate**:
   ```bash
   # Test HTTPS connection
   curl -v https://arm-proxy.maltacentral.com/api/ping
   
   # Check certificate validity
   openssl s_client -connect arm-proxy.maltacentral.com:443 -servername arm-proxy.maltacentral.com
   ```

## What Was Changed

The following files were updated to include arm-proxy.maltacentral.com in the certificate:

1. `/scripts/renew_all_certs.sh` - Added domain to certbot command
2. `Makefile` - Updated certbot-renew target
3. `/dev-docs/LETSENCRYPT-GUIDE.md` - Updated documentation
4. `/docs/SSL_CERTIFICATES.md` - Updated certificate coverage list

## Troubleshooting

If the certificate generation fails:

1. **Check DNS records**: Ensure arm-proxy.maltacentral.com has proper DNS records
2. **Verify Cloudflare API token**: Ensure it has DNS edit permissions for maltacentral.com
3. **Check rate limits**: Let's Encrypt has rate limits, wait if necessary
4. **Review logs**: Check certbot output for specific errors

## Notes

- The certificate is stored in `./certs/live/vfservices.viloforge.com/`
- All domains share the same certificate for easier management
- Traefik automatically uses the certificate for the configured domain
- The azure-rm-proxy service is already configured in docker-compose.yml with proper Traefik labels

## Changelog

- 2025-06-28T10:30:00Z: Initial setup documentation created