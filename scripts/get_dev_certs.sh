#!/usr/bin/env bash
set -euo pipefail
# Obtain certificates using certbot in Docker
docker compose run --rm certbot
