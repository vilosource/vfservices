VF_JWT_SECRET ?= change-me
DEV_DOMAIN ?= vfservices.viloforge.com
CERT_DIR ?= certs/live/$(DEV_DOMAIN)
CERT_FILE ?= $(CERT_DIR)/fullchain.pem
KEY_FILE ?= $(CERT_DIR)/privkey.pem

.PHONY: help up dev-cert https-up http-up docker-dev-up docker-dev-down docker-dev-build docker-dev-logs docker-dev-https docker-dev-certbot-renew

help:
	@echo "Available make targets:"
	@echo "  help                Show this help message"
	@echo "  up                  Run all Django apps with HTTPS (runserver_plus) on 0.0.0.0"
	@echo "  https-up            Same as 'up' (HTTPS with runserver_plus)"
	@echo "  http-up             Run all Django apps with HTTP only (runserver) on 0.0.0.0"
	@echo "  dev-cert            Generate development certificates"
	@echo "  docker-dev-up       Start all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-https    Start all dev containers with HTTPS support"
	@echo "  docker-dev-down     Stop all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-build    Build all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-logs     View logs for dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-certbot-renew  Renew Let's Encrypt certificates using Cloudflare DNS challenge"

up:
	$(MAKE) -j4 run-identity-0 run-website-0 run-billing-0 run-inventory-0

run-identity-0:
	if [ ! -f identity-provider/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python identity-provider/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python identity-provider/manage.py runserver_plus 0.0.0.0:8001 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-website-0:
	if [ ! -f website/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python website/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python website/manage.py runserver_plus 0.0.0.0:8002 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-billing-0:
	if [ ! -f billing-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python billing-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python billing-api/manage.py runserver_plus 0.0.0.0:8003 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-inventory-0:
	if [ ! -f inventory-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python inventory-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python inventory-api/manage.py runserver_plus 0.0.0.0:8004 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

device-cert:
	@echo "Deprecated target name: use dev-cert"

dev-cert:
	./scripts/get_dev_certs.sh

generate-self-signed-cert:
	./scripts/generate_dev_certs.sh

docker-dev-up:
	docker compose -f docker-compose.dev.yml up

docker-dev-down:
	docker compose -f docker-compose.dev.yml down

docker-dev-build:
	docker compose -f docker-compose.dev.yml build

docker-dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

docker-dev-https: dev-cert
	@echo "Starting services with HTTPS support..."
	@echo "Certificates should be available in ./certs/live/${DEV_DOMAIN}/"
	docker compose -f docker-compose.dev.yml up

docker-dev-certbot-renew:
	@echo "Renewing Let's Encrypt certificates..."
	@echo "This will force renewal even if the certificate is not due for renewal"
	@echo "dns_cloudflare_api_token=${CLOUDFLARE_API_TOKEN}" > /tmp/cloudflare.ini
	@chmod 600 /tmp/cloudflare.ini
	docker run --rm \
	  -v "$(PWD)/certs:/etc/letsencrypt" \
	  -v "/tmp/cloudflare.ini:/tmp/cloudflare.ini:ro" \
	  certbot/dns-cloudflare certonly \
	  --dns-cloudflare \
	  --dns-cloudflare-credentials /tmp/cloudflare.ini \
	  --email "${LETSENCRYPT_EMAIL}" \
	  --agree-tos \
	  --no-eff-email \
	  --force-renewal \
	  --non-interactive \
	  --dns-cloudflare-propagation-seconds 60 \
	  -d "${DEV_DOMAIN}" \
	  -d "*.${DEV_DOMAIN}" \
	  --cert-name "${DEV_DOMAIN}"
	@rm -f /tmp/cloudflare.ini

.DEFAULT_GOAL := help
