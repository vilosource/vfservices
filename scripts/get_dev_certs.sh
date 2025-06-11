#!/usr/bin/env bash
set -e
CERT_DIR="certs"
DOMAIN="${DEV_DOMAIN:-localhost}"
mkdir -p "$CERT_DIR"
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$CERT_DIR/privkey.pem" \
    -out "$CERT_DIR/fullchain.pem" -days 365 -subj "/CN=$DOMAIN"
echo "Certificates generated in $CERT_DIR" 
