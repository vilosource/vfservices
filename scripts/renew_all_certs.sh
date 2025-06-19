#!/usr/bin/env bash
set -euo pipefail

# Configuration
DOMAIN="${BASE_DOMAIN:-vfservices.viloforge.com}"
EMAIL="${LETSENCRYPT_EMAIL:-viloforge@outlook.com}"

# Check if required environment variables are set
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "Error: CLOUDFLARE_API_TOKEN environment variable must be set"
  echo "Run: export CLOUDFLARE_API_TOKEN=your-cloudflare-api-token"
  exit 1
fi

if [ -z "${LETSENCRYPT_EMAIL:-}" ]; then
  echo "Error: LETSENCRYPT_EMAIL environment variable must be set"
  echo "Run: export LETSENCRYPT_EMAIL=your-email@example.com"
  exit 1
fi

echo "========================================"
echo "Certificate Renewal for VF Services"
echo "========================================"
echo "Primary domain: ${DOMAIN}"
echo "Email: ${EMAIL}"
echo "Additional domains: cielo.viloforge.com"
echo ""
echo "This will obtain/renew certificates for:"
echo "  - ${DOMAIN}"
echo "  - *.${DOMAIN}"
echo "  - cielo.viloforge.com"
echo "  - *.cielo.viloforge.com"
echo "========================================"

# Create necessary directories
mkdir -p ./certs

# Create temporary cloudflare.ini with API token
echo "dns_cloudflare_api_token = ${CLOUDFLARE_API_TOKEN}" > /tmp/cloudflare.ini
chmod 600 /tmp/cloudflare.ini

# Run Certbot with all domains
echo "Running Certbot..."
docker run --rm \
  -v "$(pwd)/certs:/etc/letsencrypt" \
  -v "/tmp/cloudflare.ini:/tmp/cloudflare.ini:ro" \
  certbot/dns-cloudflare certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /tmp/cloudflare.ini \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email \
  --keep-until-expiring \
  --non-interactive \
  --dns-cloudflare-propagation-seconds 60 \
  -d "${DOMAIN}" \
  -d "*.${DOMAIN}" \
  -d "cielo.viloforge.com" \
  -d "*.cielo.viloforge.com" \
  --cert-name "${DOMAIN}"

# Remove the temporary file
rm -f /tmp/cloudflare.ini

echo ""
echo "✅ Certificates successfully obtained/renewed!"
echo "Certificate location: ./certs/live/${DOMAIN}/"
echo ""
echo "The certificate now covers:"
echo "  - ${DOMAIN} and all subdomains"
echo "  - cielo.viloforge.com and all subdomains"
echo ""
echo "You can verify the certificate domains with:"
echo "openssl x509 -in ./certs/live/${DOMAIN}/cert.pem -text -noout | grep -A2 'Subject Alternative Name'"