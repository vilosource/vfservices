VF_JWT_SECRET ?= change-me
DEV_DOMAIN ?= vfservices.viloforge.com
CERT_DIR ?= certs/live/$(DEV_DOMAIN)
CERT_FILE ?= $(CERT_DIR)/fullchain.pem
KEY_FILE ?= $(CERT_DIR)/privkey.pem

.PHONY: help up dev-cert https-up http-up docker-dev-up docker-dev-down docker-dev-build docker-dev-logs docker-dev-https docker-dev-certbot-renew db-reset db-reset-dev db-shell db-list db-drop-all fresh-start dev-reset dev-fresh dev-backup dev-shell-db dev-logs-db restart-identity restart-website restart-billing restart-inventory dev-status prod-backup prod-restore archive

help:
	@echo "Available make targets:"
	@echo ""
	@echo "=== Local Development (without Docker) ==="
	@echo "  up                  Run all Django apps with HTTPS (runserver_plus) on 0.0.0.0"
	@echo "  https-up            Same as 'up' (HTTPS with runserver_plus)"
	@echo "  http-up             Run all Django apps with HTTP only (runserver) on 0.0.0.0"
	@echo "  dev-cert            Generate development certificates"
	@echo ""
	@echo "=== Docker Development ==="
	@echo "  docker-dev-up       Start all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-https    Start all dev containers with HTTPS support"
	@echo "  docker-dev-down     Stop all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-build    Build all dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-logs     View logs for dev containers (docker-compose.dev.yml)"
	@echo "  docker-dev-certbot-renew  Renew Let's Encrypt certificates using Cloudflare DNS challenge"
	@echo ""
	@echo "=== Database Management ==="
	@echo "  dev-reset           Reset all development databases (removes volume)"
	@echo "  dev-fresh           Fresh start: reset DB, rebuild containers, start services"
	@echo "  dev-backup          Backup all development databases"
	@echo "  dev-shell-db        Open PostgreSQL shell for development"
	@echo "  dev-logs-db         Show PostgreSQL logs for development"
	@echo "  dev-status          Show development environment status"
	@echo "  db-drop-all         Drop all application databases (keep PostgreSQL running)"
	@echo "  prod-backup         Backup production databases"
	@echo "  prod-restore        Restore production databases from backup"
	@echo ""
	@echo "=== Service Management ==="
	@echo "  restart-identity    Restart identity-provider service"
	@echo "  restart-website     Restart website service"
	@echo "  restart-billing     Restart billing-api service"
	@echo "  restart-inventory   Restart inventory-api service"
	@echo ""
	@echo "=== Project Management ==="
	@echo "  archive             Create a project archive excluding .gitignore files"

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

# Database management targets
db-reset: docker-dev-down
	@echo "Removing PostgreSQL volume to reset all databases..."
	docker volume rm vfservices_pgdata 2>/dev/null || true
	@echo "All databases will be recreated on next startup"

db-drop-all:
	@echo "Dropping all application databases..."
	./scripts/manage_db.sh docker-compose.dev.yml drop-all

db-shell:
	@echo "Connecting to PostgreSQL as superuser..."
	./scripts/manage_db.sh docker-compose.dev.yml shell

db-list:
	@echo "Listing all databases..."
	./scripts/manage_db.sh docker-compose.dev.yml list

# Development workflow targets
dev-reset: 
	@echo "Resetting development environment..."
	./scripts/manage_db.sh docker-compose.dev.yml reset

dev-fresh: dev-reset docker-dev-build docker-dev-up
	@echo "Fresh development environment started!"

dev-backup:
	@echo "Backing up development databases..."
	./scripts/manage_db.sh docker-compose.dev.yml backup

dev-shell-db:
	@echo "Opening development database shell..."
	./scripts/manage_db.sh docker-compose.dev.yml shell

dev-logs-db:
	@echo "Showing PostgreSQL logs..."
	docker compose -f docker-compose.dev.yml logs -f postgres

dev-status:
	@echo "=== Development Environment Status ==="
	@echo ""
	@echo "=== Container Status ==="
	docker compose -f docker-compose.dev.yml ps
	@echo ""
	@echo "=== Database Status ==="
	./scripts/manage_db.sh docker-compose.dev.yml status 2>/dev/null || echo "PostgreSQL not running"

# Individual service management
restart-identity:
	@echo "Restarting identity-provider service..."
	docker compose -f docker-compose.dev.yml restart identity-provider

restart-website:
	@echo "Restarting website service..."
	docker compose -f docker-compose.dev.yml restart website

restart-billing:
	@echo "Restarting billing-api service..."
	docker compose -f docker-compose.dev.yml restart billing-api

restart-inventory:
	@echo "Restarting inventory-api service..."
	docker compose -f docker-compose.dev.yml restart inventory-api

# Production database management
prod-backup:
	@echo "Backing up production databases..."
	./scripts/manage_db.sh docker-compose.yml backup

prod-restore:
	@read -p "Enter backup directory path: " backup_dir; \
	echo "Restoring production databases from $$backup_dir..."; \
	./scripts/manage_db.sh docker-compose.yml restore "$$backup_dir"

# Fresh start - rebuild everything
fresh-start: docker-dev-down db-reset docker-dev-build
	@echo "Fresh environment ready. Starting services..."
	docker compose -f docker-compose.dev.yml up

# Archive project excluding .gitignore files
archive:
	@echo "Creating project archive..."
	@PROJECT_NAME=$$(basename $(PWD)); \
	ARCHIVE_NAME="$${PROJECT_NAME}-$$(date +%Y%m%d-%H%M%S).tar.gz"; \
	echo "Archive name: $$ARCHIVE_NAME"; \
	cd ..; \
	if command -v git >/dev/null 2>&1 && [ -d vfservices/.git ]; then \
		echo "Using git to create archive (excludes .gitignore files)..."; \
		cd vfservices && git archive --format=tar.gz --prefix="$$PROJECT_NAME/" HEAD > "../$$ARCHIVE_NAME"; \
		cd ..; \
	else \
		echo "Git not available or not a git repository. Using tar with .gitignore exclusions..."; \
		tar --exclude-from=vfservices/.gitignore \
		    --exclude='.git' \
		    --exclude='*.tar.gz' \
		    --exclude='*.zip' \
		    -czf "$$ARCHIVE_NAME" vfservices/; \
	fi; \
	echo "Archive created: $$PWD/$$ARCHIVE_NAME"; \
	ls -lh "$$ARCHIVE_NAME"

.DEFAULT_GOAL := help
