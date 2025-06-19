#!/usr/bin/env bash
set -euo pipefail

# Configuration
DOMAIN="${BASE_DOMAIN:-vfservices.viloforge.com}"
CERT_DIR="certs/live/${DOMAIN}"
mkdir -p "${CERT_DIR}"

# Generate a private key if it doesn't exist
if [ ! -f "${CERT_DIR}/privkey.pem" ]; then
  echo "Generating private key..."
  openssl genrsa -out "${CERT_DIR}/privkey.pem" 2048
fi

# Generate a self-signed certificate
echo "Generating self-signed certificate for *.${DOMAIN}..."
openssl req -x509 -new -nodes -key "${CERT_DIR}/privkey.pem" \
  -sha256 -days 365 \
  -out "${CERT_DIR}/fullchain.pem" \
  -subj "/CN=*.${DOMAIN}" \
  -addext "subjectAltName = DNS:${DOMAIN}, DNS:*.${DOMAIN}"

# Generate a dummy chain.pem (for compatibility)
cp "${CERT_DIR}/fullchain.pem" "${CERT_DIR}/chain.pem"
cp "${CERT_DIR}/fullchain.pem" "${CERT_DIR}/cert.pem"

echo "Development certificates generated successfully in ${CERT_DIR}:"
echo " - Private Key: ${CERT_DIR}/privkey.pem"
echo " - Certificate: ${CERT_DIR}/fullchain.pem"
echo ""
echo "Note: These are self-signed certificates for development purposes only."
echo "Your browser will show a security warning when accessing https://*.${DOMAIN}"
