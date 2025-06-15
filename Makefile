VF_JWT_SECRET ?= change-me
BASE_DOMAIN ?= vfservices.viloforge.com
CERT_DIR ?= certs/live/$(BASE_DOMAIN)
CERT_FILE ?= $(CERT_DIR)/fullchain.pem
KEY_FILE ?= $(CERT_DIR)/privkey.pem

# Enhanced testing variables
TEST_RUN_ID ?= $(shell date +%Y%m%d_%H%M%S)
TEST_TARGET ?= development
TEST_MODE ?= full
TEST_PARALLEL ?= 4
TEST_TIMEOUT ?= 30000
TEST_WEB_PORT ?= 8080

.PHONY: help up dev-cert https-up http-up docker-dev-up docker-dev-down docker-dev-build docker-dev-logs docker-dev-https docker-dev-certbot-renew db-reset db-reset-dev db-shell db-list db-drop-all fresh-start dev-reset dev-fresh dev-backup dev-shell-db dev-logs-db restart-identity restart-website restart-billing restart-inventory dev-status prod-backup prod-restore archive test test-setup test-ui test-headed test-debug test-docker test-ci test-docker-enhanced test-docker-setup test-docker-run test-docker-headed test-docker-debug test-docker-clean test-analyze test-report test-archive test-monitor test-web test-quick test-ci-docker test-status test-list test-help

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
	@echo "=== Testing ==="
	@echo "  test-setup          Install test dependencies and setup environment"
	@echo "  test                Run all Playwright tests (legacy - use test-docker-enhanced)"
	@echo "  test-docker         Run tests using Docker (legacy)"
	@echo "  test-ui             Run tests in interactive UI mode"
	@echo "  test-headed         Run tests in headed mode (visible browser)"
	@echo "  test-debug          Run tests in debug mode"
	@echo "  test-ci             Run tests in CI mode (GitHub Actions compatible)"
	@echo ""
	@echo "=== Enhanced Docker Testing ==="
	@echo "  test-docker-enhanced    Full test run with analysis (recommended)"
	@echo "  test-docker-headed      Visual debugging with browser UI"
	@echo "  test-docker-debug       Interactive debug shell"
	@echo "  test-quick              Quick smoke tests"
	@echo "  test-ci-docker          CI-optimized testing"
	@echo "  test-analyze            Analyze specific test run"
	@echo "  test-web                Start web server for reports"
	@echo "  test-status             Show test environment status"
	@echo "  test-help               Show detailed testing help"
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
	SSO_COOKIE_DOMAIN=.${BASE_DOMAIN} \
	PYTHONPATH=$(PWD) python identity-provider/manage.py runserver_plus 0.0.0.0:8001 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-website-0:
	if [ ! -f website/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python website/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${BASE_DOMAIN} \
	PYTHONPATH=$(PWD) python website/manage.py runserver_plus 0.0.0.0:8002 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-billing-0:
	if [ ! -f billing-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python billing-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${BASE_DOMAIN} \
	PYTHONPATH=$(PWD) python billing-api/manage.py runserver_plus 0.0.0.0:8003 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-inventory-0:
	if [ ! -f inventory-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python inventory-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${BASE_DOMAIN} \
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
	@echo "Certificates should be available in ./certs/live/${BASE_DOMAIN}/"
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
	  -d "${BASE_DOMAIN}" \
	  -d "*.${BASE_DOMAIN}" \
	  --cert-name "${BASE_DOMAIN}"
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

# Legacy testing targets (for compatibility)
_legacy-test-setup:
	@echo "Setting up legacy test environment..."
	@if [ ! -f tests/.env ]; then \
		echo "Creating default test environment file..."; \
		$(MAKE) _create-test-env; \
	fi
	@echo "Installing test dependencies..."
	cd tests && npm install
	@echo "Installing Playwright browsers..."
	cd tests && npx playwright install
	@echo "Legacy test environment setup complete!"

test: _legacy-test-setup
	@echo "Running Playwright tests..."
	@echo "Note: This is legacy testing. Use 'make test-docker-enhanced' for the enhanced Docker-based testing."
	@echo "Ensuring services are running..."
	@docker compose ps traefik >/dev/null 2>&1 || { echo "Starting services..."; docker compose up -d; sleep 15; }
	@echo "Note: If you encounter browser dependency issues, use 'make test-docker-enhanced' for containerized testing"
	cd tests && npm test

test-ui: _legacy-test-setup
	@echo "Running Playwright tests in UI mode..."
	@docker compose ps traefik >/dev/null 2>&1 || { echo "Starting services..."; docker compose up -d; sleep 10; }
	cd tests && npm run test:ui

test-headed: _legacy-test-setup
	@echo "Running Playwright tests in headed mode..."
	@docker compose ps traefik >/dev/null 2>&1 || { echo "Starting services..."; docker compose up -d; sleep 10; }
	cd tests && npm run test:headed

test-debug: _legacy-test-setup
	@echo "Running Playwright tests in debug mode..."
	@docker compose ps traefik >/dev/null 2>&1 || { echo "Starting services..."; docker compose up -d; sleep 10; }
	cd tests && npm run test:debug

test-docker:
	@echo "Running tests using Docker..."
	@echo "Note: This is the legacy Docker testing. Use 'make test-docker-enhanced' for the enhanced version."
	@echo "Starting all services including test runner..."
	docker compose -f docker-compose.yml -f docker-compose.test.yml up --build playwright

test-ci:
	@echo "Running tests in CI mode..."
	@if [ ! -f tests/.env ]; then \
		echo "Creating CI test environment file..."; \
		$(MAKE) _create-test-env; \
	fi
	cd tests && npm ci
	cd tests && npx playwright install --with-deps
	cd tests && CI=true npx playwright test --reporter=github

_create-test-env:
	@echo "# Auto-generated test environment file" > tests/.env
	@echo "# Based on docker-compose.yml variables" >> tests/.env
	@echo "" >> tests/.env
	@echo "# Environment configuration" >> tests/.env
	@echo "NODE_ENV=test" >> tests/.env
	@echo "TEST_ENV=development" >> tests/.env
	@echo "" >> tests/.env
	@echo "# Service URLs (using BASE_DOMAIN from docker-compose)" >> tests/.env
	@echo "BASE_URL=https://$(BASE_DOMAIN)" >> tests/.env
	@echo "IDENTITY_URL=https://identity.$(BASE_DOMAIN)" >> tests/.env
	@echo "WEBSITE_URL=https://website.$(BASE_DOMAIN)" >> tests/.env
	@echo "BILLING_URL=https://billing.$(BASE_DOMAIN)" >> tests/.env
	@echo "INVENTORY_URL=https://inventory.$(BASE_DOMAIN)" >> tests/.env
	@echo "" >> tests/.env
	@echo "# Playwright configuration" >> tests/.env
	@echo "PWDEBUG=0" >> tests/.env
	@echo "PLAYWRIGHT_BROWSERS_PATH=/ms-playwright" >> tests/.env
	@echo "" >> tests/.env
	@echo "# Test credentials (from docker-compose defaults)" >> tests/.env
	@echo "TEST_ADMIN_USERNAME=admin" >> tests/.env
	@echo "TEST_ADMIN_PASSWORD=admin123" >> tests/.env
	@echo "TEST_USER_USERNAME=testuser" >> tests/.env
	@echo "TEST_USER_PASSWORD=testpass123" >> tests/.env
	@echo "" >> tests/.env
	@echo "# Database configuration (for API tests)" >> tests/.env
	@echo "POSTGRES_HOST=postgres" >> tests/.env
	@echo "POSTGRES_USER=vfuser" >> tests/.env
	@echo "POSTGRES_PASSWORD=vfpass" >> tests/.env
	@echo "POSTGRES_DB=vfdb" >> tests/.env

# =============================================================================
# ENHANCED DOCKER-BASED TESTING WITH RESULT PERSISTENCE
# =============================================================================

# Setup Docker test environment
test-docker-setup:
	@echo "🚀 Setting up enhanced Docker test environment..."
	@echo "Test Run ID: $(TEST_RUN_ID)"
	@echo "Base Domain: $(BASE_DOMAIN)"
	@mkdir -p test-results test-reports analysis-output public-reports
	@docker network create vfnet 2>/dev/null || true
	@echo "📦 Building enhanced test containers..."
	@docker compose -f docker-compose.test.enhanced.yml build --build-arg TEST_TARGET=$(TEST_TARGET)
	@echo "✅ Test environment setup complete"

# Full enhanced test run with comprehensive result persistence
test-docker-enhanced: test-docker-setup
	@echo "🧪 Running enhanced Docker-based tests with full analysis..."
	@echo "==============================================="
	@echo "Test Configuration:"
	@echo "  Run ID: $(TEST_RUN_ID)"
	@echo "  Target: $(TEST_TARGET)"
	@echo "  Mode: $(TEST_MODE)"
	@echo "  Domain: $(BASE_DOMAIN)"
	@echo "  Parallel: $(TEST_PARALLEL)"
	@echo "==============================================="
	@mkdir -p test-results/$(TEST_RUN_ID)
	@echo "🚀 Starting VF Services..."
	@docker compose up -d
	@sleep 20
	@echo "🧪 Running tests with result persistence..."
	@docker compose -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$(TEST_RUN_ID) \
		-e TEST_TARGET=$(TEST_TARGET) \
		-e TEST_MODE=$(TEST_MODE) \
		-e TEST_PARALLEL=$(TEST_PARALLEL) \
		-e TEST_TIMEOUT=$(TEST_TIMEOUT) \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner || \
		(echo "❌ Tests failed - generating failure analysis..." && \
		 $(MAKE) test-analyze TEST_RUN_ID=$(TEST_RUN_ID) && exit 1)
	@echo "📊 Generating test analysis..."
	@$(MAKE) test-analyze TEST_RUN_ID=$(TEST_RUN_ID)
	@echo "✅ Enhanced test run complete!"
	@echo "📁 Results saved to: test-results/$(TEST_RUN_ID)"
	@echo "📊 Reports available at: test-reports/"

# Headed mode for visual debugging
test-docker-headed: test-docker-setup
	@echo "🖥️ Running tests in headed mode (requires X11 forwarding)..."
	@if [ -n "$$DISPLAY" ]; then \
		xhost +local:docker 2>/dev/null || true; \
	else \
		echo "⚠️ Warning: DISPLAY not set - headed mode may not work"; \
	fi
	@export TEST_RUN_ID=$(TEST_RUN_ID)_headed && \
	export TEST_MODE=headed && \
	export PWDEBUG=1 && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 20 && \
	docker compose -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e TEST_MODE=headed \
		-e PWDEBUG=1 \
		-e DISPLAY=${DISPLAY} \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner

# Interactive debug mode with shell access
test-docker-debug: test-docker-setup
	@echo "🐛 Starting interactive debug container..."
	@docker compose up -d
	@sleep 20
	@echo "🔍 Entering debug shell - run tests manually or investigate issues"
	@echo "Available commands:"
	@echo "  npm test                    - Run all tests"
	@echo "  npm run test:headed         - Run with browser UI"
	@echo "  npm run test:debug          - Run in debug mode"
	@echo "  curl -k https://$(BASE_DOMAIN)/api/status/  - Test service"
	@docker compose -f docker-compose.test.enhanced.yml --profile testing run --rm -it \
		-e TEST_MODE=debug \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		--entrypoint=/bin/bash \
		playwright-runner

# Analyze test results with comprehensive reporting
test-analyze:
	@echo "📊 Analyzing test results for run: $(TEST_RUN_ID)"
	@if [ -z "$(TEST_RUN_ID)" ]; then \
		echo "❌ Error: TEST_RUN_ID not provided"; \
		echo "Usage: make test-analyze TEST_RUN_ID=<run_id>"; \
		echo "Available runs:"; \
		ls -la test-results/ 2>/dev/null || echo "No test results found"; \
		exit 1; \
	fi
	@if [ ! -d "test-results/$(TEST_RUN_ID)" ]; then \
		echo "❌ Error: Test results directory not found: test-results/$(TEST_RUN_ID)"; \
		echo "Available runs:"; \
		ls -la test-results/ 2>/dev/null || echo "No test results found"; \
		exit 1; \
	fi
	@echo "🔍 Running comprehensive analysis..."
	@docker compose -f docker-compose.test.enhanced.yml --profile analysis run --rm \
		-e TEST_RUN_ID=$(TEST_RUN_ID) \
		test-analyzer
	@echo "✅ Analysis complete for run: $(TEST_RUN_ID)"
	@echo "📁 Analysis results: test-reports/$(TEST_RUN_ID)_analysis.html"

# Generate comprehensive test reports
test-report:
	@echo "📋 Generating comprehensive test reports..."
	@docker compose -f docker-compose.test.enhanced.yml --profile reporting run --rm \
		-e REPORT_TYPE=comprehensive \
		report-generator
	@echo "✅ Comprehensive reports generated"
	@echo "📁 Reports available in: public-reports/"

# Start web server for viewing test reports
test-web:
	@echo "🌐 Starting test results web server..."
	@echo "📊 Test reports will be available at: http://localhost:$(TEST_WEB_PORT)"
	@echo "📁 Direct report access:"
	@echo "  http://localhost:$(TEST_WEB_PORT)/reports/     - Analysis reports"
	@echo "  http://localhost:$(TEST_WEB_PORT)/public/      - Public reports"
	@docker compose -f docker-compose.test.enhanced.yml --profile web up -d test-web-server
	@echo "✅ Web server started on port $(TEST_WEB_PORT)"

# Stop web server
test-web-stop:
	@echo "🛑 Stopping test results web server..."
	@docker compose -f docker-compose.test.enhanced.yml --profile web down
	@echo "✅ Web server stopped"

# Monitor test results in real-time
test-monitor:
	@echo "👁️ Starting real-time test monitoring..."
	@echo "This will watch for changes in test results and trigger analysis"
	@docker compose -f docker-compose.test.enhanced.yml --profile monitoring up test-monitor

# Archive test results for long-term storage
test-archive:
	@echo "📦 Archiving test results..."
	@if [ -z "$(TEST_RUN_ID)" ]; then \
		ARCHIVE_NAME="test-results-all-$(shell date +%Y%m%d_%H%M%S).tar.gz"; \
		echo "📁 Creating complete archive: $$ARCHIVE_NAME"; \
		tar -czf "$$ARCHIVE_NAME" test-results/ test-reports/ analysis-output/ 2>/dev/null || true; \
	else \
		ARCHIVE_NAME="test-results-$(TEST_RUN_ID)-$(shell date +%Y%m%d_%H%M%S).tar.gz"; \
		echo "📁 Creating archive for run $(TEST_RUN_ID): $$ARCHIVE_NAME"; \
		tar -czf "$$ARCHIVE_NAME" \
			test-results/$(TEST_RUN_ID)/ \
			test-reports/$(TEST_RUN_ID)* \
			2>/dev/null || true; \
	fi && \
	echo "✅ Archive created: $$ARCHIVE_NAME" && \
	ls -lh "$$ARCHIVE_NAME"

# Clean up test containers and volumes
test-docker-clean:
	@echo "🧹 Cleaning up Docker test environment..."
	@docker compose -f docker-compose.test.enhanced.yml down -v --remove-orphans
	@docker system prune -f --filter label=testing=playwright 2>/dev/null || true
	@echo "✅ Test environment cleaned"

# Clean test results (with confirmation)
test-clean-results:
	@echo "⚠️ This will delete ALL test results and reports!"
	@read -p "Are you sure? (y/N): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo "🗑️ Removing test results..."; \
		rm -rf test-results/* test-reports/* analysis-output/* public-reports/* 2>/dev/null || true; \
		echo "✅ Test results cleaned"; \
	else \
		echo "❌ Operation cancelled"; \
	fi

# =============================================================================
# CI/CD OPTIMIZED TESTING
# =============================================================================

# CI-optimized testing with GitHub Actions integration
test-ci-docker: test-docker-setup
	@echo "🏗️ Running CI-optimized Docker tests..."
	@export TEST_RUN_ID=ci_$(shell date +%Y%m%d_%H%M%S) && \
	export TEST_TARGET=production && \
	export CI=true && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	echo "📊 CI Test Configuration:" && \
	echo "  Run ID: $$TEST_RUN_ID" && \
	echo "  Target: production" && \
	echo "  CI Mode: enabled" && \
	docker compose up -d && \
	sleep 25 && \
	docker compose -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e TEST_TARGET=production \
		-e CI=true \
		-e GITHUB_ACTIONS=${GITHUB_ACTIONS} \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner && \
	echo "📊 Generating CI analysis..." && \
	$(MAKE) test-analyze TEST_RUN_ID=$$TEST_RUN_ID || \
	(echo "❌ CI tests failed - generating failure report" && \
	 $(MAKE) test-analyze TEST_RUN_ID=$$TEST_RUN_ID && exit 1)

# =============================================================================
# UTILITY TARGETS
# =============================================================================

# Show test status and recent results
test-status:
	@echo "📊 VF Services Test Status"
	@echo "=========================="
	@echo ""
	@echo "🐳 Docker Environment:"
	@docker compose ps 2>/dev/null || echo "❌ Services not running"
	@echo ""
	@echo "📁 Recent Test Runs:"
	@ls -la test-results/ 2>/dev/null | head -10 || echo "❌ No test results found"
	@echo ""
	@echo "📊 Test Reports:"
	@ls -la test-reports/ 2>/dev/null | head -5 || echo "❌ No reports found"
	@echo ""
	@echo "🌐 Web Server Status:"
	@docker compose -f docker-compose.test.enhanced.yml --profile web ps 2>/dev/null || echo "❌ Web server not running"

# Quick test run (for development)
test-quick:
	@echo "⚡ Running quick test subset..."
	@export TEST_RUN_ID=quick_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 15 && \
	docker compose -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test -- --grep="@smoke" --output-dir=/test-results/$$TEST_RUN_ID

# List available test runs
test-list:
	@echo "📋 Available Test Runs:"
	@echo "======================"
	@if [ -d "test-results" ]; then \
		for dir in test-results/*/; do \
			if [ -d "$$dir" ]; then \
				run_id=$$(basename "$$dir"); \
				size=$$(du -sh "$$dir" 2>/dev/null | cut -f1); \
				modified=$$(stat -c %y "$$dir" 2>/dev/null | cut -d' ' -f1); \
				echo "  $$run_id ($$size, $$modified)"; \
			fi; \
		done; \
	else \
		echo "❌ No test results directory found"; \
	fi

# Show help for enhanced testing
test-help:
	@echo "🧪 Enhanced Docker Testing Commands"
	@echo "===================================="
	@echo ""
	@echo "🚀 Main Testing:"
	@echo "  test-docker-enhanced    - Full test run with analysis (recommended)"
	@echo "  test-docker-headed      - Visual debugging with browser UI"
	@echo "  test-docker-debug       - Interactive debug shell"
	@echo "  test-quick              - Quick smoke tests"
	@echo ""
	@echo "📊 Analysis & Reporting:"
	@echo "  test-analyze           - Analyze specific test run"
	@echo "  test-report            - Generate comprehensive reports"
	@echo "  test-web               - Start web server for reports"
	@echo "  test-monitor           - Real-time result monitoring"
	@echo ""
	@echo "🏗️ CI/CD:"
	@echo "  test-ci-docker         - Optimized CI testing"
	@echo ""
	@echo "🛠️ Utilities:"
	@echo "  test-status            - Show current test status"
	@echo "  test-list              - List available test runs"
	@echo "  test-archive           - Archive test results"
	@echo "  test-docker-clean      - Clean Docker environment"
	@echo "  test-clean-results     - Clean test results (with confirmation)"
	@echo ""
	@echo "📝 Examples:"
	@echo "  make test-docker-enhanced                    - Full test run"
	@echo "  make test-analyze TEST_RUN_ID=20241215_143022  - Analyze specific run"
	@echo "  make test-docker-headed                      - Debug with browser UI"
	@echo "  make test-web TEST_WEB_PORT=8080            - Start report server"
	@echo ""
	@echo "🔧 Variables:"
	@echo "  TEST_RUN_ID     - Specific test run identifier"
	@echo "  TEST_TARGET     - development|production|ci"
	@echo "  TEST_MODE       - full|headed|debug|quick"
	@echo "  BASE_DOMAIN     - Domain for services (default: vfservices.viloforge.com)"
	@echo "  TEST_WEB_PORT   - Port for web report server (default: 8080)"

# =============================================================================
# ENHANCED COMPATIBILITY AND SETUP
# =============================================================================

# Enhanced test-setup that includes Docker preparation
test-setup: 
	@echo "🔧 Setting up comprehensive test environment..."
	@$(MAKE) test-docker-setup
	@echo "📦 Installing local test dependencies..."
	@if [ ! -f tests/.env ]; then \
		echo "📝 Creating default test environment file..."; \
		$(MAKE) _create-test-env; \
	fi
	@cd tests && npm install
	@cd tests && npx playwright install
	@echo "✅ Complete test environment setup finished!"
	@echo "💡 Tip: Use 'make test-docker-enhanced' for containerized testing"

.DEFAULT_GOAL := help
