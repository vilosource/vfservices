#!/usr/bin/env bash
set -euo pipefail
DOMAIN="${DEV_DOMAIN:-vfservices.viloforge.com}"
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is required}"
: "${LETSENCRYPT_EMAIL:?LETSENCRYPT_EMAIL is required}"
echo "dns_cloudflare_api_token=${CLOUDFLARE_API_TOKEN}" > /tmp/cloudflare.ini
chmod 600 /tmp/cloudflare.ini
certbot certonly --dns-cloudflare --dns-cloudflare-credentials /tmp/cloudflare.ini \
  -d "*.${DOMAIN}" -d "${DOMAIN}" \
  --agree-tos --no-eff-email -m "${LETSENCRYPT_EMAIL}" --non-interactive \
  --dns-cloudflare-propagation-seconds 60
