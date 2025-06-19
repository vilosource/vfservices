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

echo "Running Certbot to obtain certificates for ${DOMAIN}, *.${DOMAIN}, cielo.viloforge.com, and *.cielo.viloforge.com..."
echo "Using Cloudflare DNS validation with the provided API token"

# Create necessary directories
mkdir -p ./certs

# Create temporary cloudflare.ini with API token
echo "dns_cloudflare_api_token = ${CLOUDFLARE_API_TOKEN}" > /tmp/cloudflare.ini
chmod 600 /tmp/cloudflare.ini

# Run Certbot directly with Docker instead of using the service
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

echo "Certificates successfully obtained and stored in ./certs/live/${DOMAIN}/"
echo "You can now run 'make docker-dev-https' to start the services with HTTPS"
