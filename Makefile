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

.PHONY: help up cert https-up http-up docker-up docker-down docker-build docker-logs docker-https certbot-renew db-reset db-shell db-list db-drop-all fresh-start db-fresh db-backup db-logs db-status db-restore restart-identity restart-website restart-billing restart-inventory archive test test-setup test-ui test-headed test-debug test-docker test-ci test-docker-enhanced test-docker-setup test-docker-run test-docker-headed test-docker-debug test-docker-clean test-analyze test-report test-archive test-monitor test-web test-quick test-ci-docker test-status test-list test-help test-cielo test-cielo-smoke test-cielo-integration test-cielo-all test-azure-costs test-billing test-cross-service test-cielo-help test-cielo-setup test-cielo-status test-identity-admin test-identity-admin-users test-identity-admin-roles test-identity-admin-bulk test-identity-admin-integration _check-services

help:
	@echo "Available make targets:"
	@echo ""
	@echo "=== Local Development (without Docker) ==="
	@echo "  up                  Run all Django apps with HTTPS (runserver_plus) on 0.0.0.0"
	@echo "  https-up            Same as 'up' (HTTPS with runserver_plus)"
	@echo "  http-up             Run all Django apps with HTTP only (runserver) on 0.0.0.0"
	@echo "  cert                Generate certificates for BASE_DOMAIN"
	@echo ""
	@echo "=== Docker Operations ==="
	@echo "  docker-up           Start all containers"
	@echo "  docker-https        Start all containers with HTTPS support"
	@echo "  docker-down         Stop all containers"
	@echo "  docker-build        Build all containers"
	@echo "  docker-logs         View logs for containers"
	@echo ""
	@echo "=== Certificate Management ==="
	@echo "  cert                Generate or retrieve certificates (auto-detects method)"
	@echo "  generate-self-signed-cert  Generate self-signed certificates"
	@echo "  certbot-renew       Renew Let's Encrypt certificates using Cloudflare DNS"
	@echo ""
	@echo "=== Database Management ==="
	@echo "  db-reset            Reset all databases (removes volume)"
	@echo "  db-fresh            Fresh start: reset DB, rebuild containers, start services"
	@echo "  db-backup           Backup all databases"
	@echo "  db-shell            Open PostgreSQL shell"
	@echo "  db-logs             Show PostgreSQL logs"
	@echo "  db-status           Show database environment status"
	@echo "  db-list             List all databases"
	@echo "  db-drop-all         Drop all application databases (keep PostgreSQL running)"
	@echo "  db-restore          Restore databases from backup"
	@echo "  fresh-start         Complete fresh start (alias for db-fresh)"
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
	@echo "=== Development Testing (Fast Feedback) ==="
	@echo "  test-smoke              Quick smoke tests (~30s)"
	@echo "  test-dev                Development subset (Chrome only, ~2min)"
	@echo "  test-critical           Critical path tests (~5min)"
	@echo "  test-auth               Authentication tests only"
	@echo "  test-api                API tests only (fastest)"
	@echo "  test-ui                 UI tests only"
	@echo "  test-chrome             Single browser tests (Chrome)"
	@echo ""
	@echo "=== Specific Test Execution ==="
	@echo "  test-file FILE=path     Run specific test file"
	@echo "  test-dir DIR=auth       Run all tests in directory"
	@echo "  test-grep PATTERN=text  Run tests matching pattern"
	@echo "  test-specific FILE= TEST=  Run specific test by name"
	@echo "  test-ls                 List available tests and directories"
	@echo ""
	@echo "=== Enhanced Docker Testing ==="
	@echo "  test-docker-enhanced    Full test run with analysis (recommended)"
	@echo "  test-docker-headed      Visual debugging with browser UI"
	@echo "  test-docker-debug       Interactive debug shell"
	@echo "  test-ci-docker          CI-optimized testing"
	@echo "  test-analyze            Analyze specific test run"
	@echo "  test-web                Start web server for reports"
	@echo "  test-status             Show test environment status"
	@echo "  test-help               Show detailed testing help"
	@echo ""
	@echo "=== CIELO Website Testing ==="
	@echo "  test-cielo              Run all CIELO website tests"
	@echo "  test-cielo-smoke        Run CIELO smoke tests only"
	@echo "  test-cielo-integration  Run CIELO integration tests only"
	@echo "  test-azure-costs        Test Azure Costs cross-service auth"
	@echo "  test-billing            Test Billing API cross-service auth"
	@echo "  test-cross-service      Test all cross-service authentication"
	@echo "  test-cielo-help         Show CIELO testing help"
	@echo ""
	@echo "Identity Provider Admin API Testing:"
	@echo "  test-identity-admin     Run all Identity Provider admin API tests"
	@echo "  test-identity-admin-users    Test user management APIs"
	@echo "  test-identity-admin-roles    Test role management APIs"
	@echo "  test-identity-admin-bulk     Test bulk operations"
	@echo "  test-identity-admin-integration Test integration scenarios"
	@echo ""
	@echo "=== Project Management ==="
	@echo "  archive             Create a project archive excluding .gitignore files"
	@echo ""
	@echo "=== Environment Variables ==="
	@echo "  BASE_DOMAIN         Domain for all services (default: vfservices.viloforge.com)"
	@echo "  VF_JWT_SECRET       JWT secret for authentication (default: change-me)"
	@echo "  POSTGRES_USER       PostgreSQL username (default: vfuser)"
	@echo "  POSTGRES_PASSWORD   PostgreSQL password (default: vfpass)"
	@echo "  CLOUDFLARE_API_TOKEN  Token for Let's Encrypt DNS challenge"
	@echo "  LETSENCRYPT_EMAIL   Email for Let's Encrypt certificates"
	@echo ""
	@echo "Example usage:"
	@echo "  make docker-up                     # Start with default domain"
	@echo "  BASE_DOMAIN=mycompany.com make docker-up  # Start with custom domain"
	@echo "  make db-fresh                      # Reset and start fresh"
	@echo "  make test-docker-enhanced          # Run comprehensive tests"

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

cert:
	./scripts/renew_all_certs.sh

generate-self-signed-cert:
	./scripts/generate_certs.sh

docker-up:
	docker compose up

docker-down:
	docker compose down

docker-build:
	docker compose build

docker-logs:
	docker compose logs -f

docker-https: cert
	@echo "Starting services with HTTPS support..."
	@echo "Certificates should be available in ./certs/live/${BASE_DOMAIN}/"
	docker compose up

certbot-renew:
	@echo "Renewing Let's Encrypt certificates..."
	@echo "This will force renewal even if the certificate is not due for renewal"
	@echo "Domains: ${BASE_DOMAIN}, *.${BASE_DOMAIN}, cielo.viloforge.com, *.cielo.viloforge.com"
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
	  -d "cielo.viloforge.com" \
	  -d "*.cielo.viloforge.com" \
	  --cert-name "${BASE_DOMAIN}"
	@rm -f /tmp/cloudflare.ini

# Database management targets
db-reset: docker-down
	@echo "Removing PostgreSQL volume to reset all databases..."
	docker volume rm vfservices_pgdata 2>/dev/null || true
	@echo "All databases will be recreated on next startup"

db-drop-all:
	@echo "Dropping all application databases..."
	./scripts/manage_db.sh docker-compose.yml drop-all

db-shell:
	@echo "Connecting to PostgreSQL as superuser..."
	./scripts/manage_db.sh docker-compose.yml shell

db-list:
	@echo "Listing all databases..."
	./scripts/manage_db.sh docker-compose.yml list

# Database workflow targets
db-fresh: db-reset docker-build docker-up
	@echo "Fresh environment started!"

db-backup:
	@echo "Backing up databases..."
	./scripts/manage_db.sh docker-compose.yml backup

db-logs:
	@echo "Showing PostgreSQL logs..."
	docker compose logs -f postgres

db-status:
	@echo "=== Environment Status ==="
	@echo ""
	@echo "=== Container Status ==="
	docker compose ps
	@echo ""
	@echo "=== Database Status ==="
	./scripts/manage_db.sh docker-compose.yml status 2>/dev/null || echo "PostgreSQL not running"

db-restore:
	@read -p "Enter backup directory path: " backup_dir; \
	echo "Restoring databases from $$backup_dir..."; \
	./scripts/manage_db.sh docker-compose.yml restore "$$backup_dir"

# Individual service management
restart-identity:
	@echo "Restarting identity-provider service..."
	docker compose restart identity-provider

restart-website:
	@echo "Restarting website service..."
	docker compose restart website

restart-billing:
	@echo "Restarting billing-api service..."
	docker compose restart billing-api

restart-inventory:
	@echo "Restarting inventory-api service..."
	docker compose restart inventory-api

# Fresh start - rebuild everything
fresh-start: docker-down db-reset docker-build
	@echo "Fresh environment ready. Starting services..."
	docker compose up

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

test-ui-legacy: _legacy-test-setup
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml build --build-arg TEST_TARGET=$(TEST_TARGET)
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
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
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm -it \
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile analysis run --rm \
		-e TEST_RUN_ID=$(TEST_RUN_ID) \
		test-analyzer
	@echo "✅ Analysis complete for run: $(TEST_RUN_ID)"
	@echo "📁 Analysis results: test-reports/$(TEST_RUN_ID)_analysis.html"

# Generate comprehensive test reports
test-report:
	@echo "📋 Generating comprehensive test reports..."
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile reporting run --rm \
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile web up -d test-web-server
	@echo "✅ Web server started on port $(TEST_WEB_PORT)"

# Stop web server
test-web-stop:
	@echo "🛑 Stopping test results web server..."
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile web down
	@echo "✅ Web server stopped"

# Monitor test results in real-time
test-monitor:
	@echo "👁️ Starting real-time test monitoring..."
	@echo "This will watch for changes in test results and trigger analysis"
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile monitoring up test-monitor

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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml down -v --remove-orphans
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
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
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
	@docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile web ps 2>/dev/null || echo "❌ Web server not running"

# =============================================================================
# DEVELOPMENT-OPTIMIZED TESTING
# =============================================================================

# Quick smoke tests (fastest - ~30 seconds)
test-smoke:
	@echo "💨 Running smoke tests (fast development feedback)..."
	@export TEST_RUN_ID=smoke_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:smoke

# Fast development tests (Chrome only - ~2 minutes)
test-dev:
	@echo "🚀 Running development test subset (Chrome only)..."
	@export TEST_RUN_ID=dev_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:dev

# Critical path tests only (~5 minutes)
test-critical:
	@echo "🎯 Running critical path tests..."
	@export TEST_RUN_ID=critical_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 15 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:critical

# Authentication tests only
test-auth:
	@echo "🔐 Running authentication tests..."
	@export TEST_RUN_ID=auth_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:auth

# API tests only (fast)
test-api:
	@echo "🔌 Running API tests..."
	@export TEST_RUN_ID=api_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 5 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:api

# UI tests only
test-ui:
	@echo "🖼️ Running UI tests..."
	@export TEST_RUN_ID=ui_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:ui-only

# Single browser tests for development (Chrome only)
test-chrome:
	@echo "🔍 Running tests on Chrome only..."
	@export TEST_RUN_ID=chrome_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:chrome

# =============================================================================
# SPECIFIC TEST EXECUTION
# =============================================================================

# Run specific test file
# Usage: make test-file FILE=auth/login.spec.js
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "❌ Error: FILE parameter required"; \
		echo "Usage: make test-file FILE=auth/login.spec.js"; \
		echo "Available test files:"; \
		find tests/playwright/tests -name "*.spec.js" | sed 's|tests/playwright/tests/||' | sort; \
		exit 1; \
	fi
	@echo "🎯 Running specific test file: $(FILE)"
	@export TEST_RUN_ID=file_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:specific -- tests/playwright/tests/$(FILE)

# Run tests matching specific pattern
# Usage: make test-grep PATTERN="login.*successfully"
test-grep:
	@if [ -z "$(PATTERN)" ]; then \
		echo "❌ Error: PATTERN parameter required"; \
		echo "Usage: make test-grep PATTERN='login.*successfully'"; \
		echo "Examples:"; \
		echo "  make test-grep PATTERN='login'"; \
		echo "  make test-grep PATTERN='should.*successfully'"; \
		echo "  make test-grep PATTERN='@smoke.*login'"; \
		exit 1; \
	fi
	@echo "🔍 Running tests matching pattern: $(PATTERN)"
	@export TEST_RUN_ID=grep_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:grep -- "$(PATTERN)"

# Run specific test by name and file
# Usage: make test-specific FILE=auth/login.spec.js TEST="should login successfully"
test-specific:
	@if [ -z "$(FILE)" ] || [ -z "$(TEST)" ]; then \
		echo "❌ Error: Both FILE and TEST parameters required"; \
		echo "Usage: make test-specific FILE=auth/login.spec.js TEST='should login successfully'"; \
		echo "Available test files:"; \
		find tests/playwright/tests -name "*.spec.js" | sed 's|tests/playwright/tests/||' | sort; \
		exit 1; \
	fi
	@echo "🎯 Running specific test: '$(TEST)' in $(FILE)"
	@export TEST_RUN_ID=specific_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:specific -- tests/playwright/tests/$(FILE) --grep="$(TEST)"

# Run tests in specific directory
# Usage: make test-dir DIR=auth
test-dir:
	@if [ -z "$(DIR)" ]; then \
		echo "❌ Error: DIR parameter required"; \
		echo "Usage: make test-dir DIR=auth"; \
		echo "Available test directories:"; \
		find tests/playwright/tests -type d -mindepth 1 | sed 's|tests/playwright/tests/||' | sort; \
		exit 1; \
	fi
	@echo "📁 Running tests in directory: $(DIR)"
	@export TEST_RUN_ID=dir_$(shell date +%Y%m%d_%H%M%S) && \
	mkdir -p test-results/$$TEST_RUN_ID && \
	docker compose up -d && \
	sleep 10 && \
	docker compose -f docker-compose.yml -f docker-compose.test.enhanced.yml --profile testing run --rm \
		-e TEST_RUN_ID=$$TEST_RUN_ID \
		-e BASE_DOMAIN=$(BASE_DOMAIN) \
		playwright-runner npm run test:specific -- tests/playwright/tests/$(DIR)/

# List available tests
test-ls:
	@echo "📋 Available Test Files:"
	@echo "======================="
	@find tests/playwright/tests -name "*.spec.js" | sed 's|tests/playwright/tests/||' | sort
	@echo ""
	@echo "📁 Available Test Directories:"
	@echo "=============================="
	@find tests/playwright/tests -type d -mindepth 1 | sed 's|tests/playwright/tests/||' | sort
	@echo ""
	@echo "🏷️ Usage Examples:"
	@echo "  make test-file FILE=auth/login.spec.js"
	@echo "  make test-dir DIR=auth"
	@echo "  make test-grep PATTERN='login'"
	@echo "  make test-specific FILE=auth/login.spec.js TEST='should login successfully'"

# Quick test run (legacy - now points to test-dev)
test-quick: test-dev

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
	@echo "⚡ Development Testing (Fast Feedback):"
	@echo "  test-smoke              - Smoke tests (~30s, fastest feedback)"
	@echo "  test-dev                - Dev subset (Chrome only, ~2min)"
	@echo "  test-critical           - Critical path (~5min)"
	@echo "  test-auth               - Authentication tests only"
	@echo "  test-api                - API tests only (fastest)"
	@echo "  test-ui                 - UI tests only"
	@echo "  test-chrome             - Single browser (Chrome)"
	@echo ""
	@echo "🚀 Main Testing:"
	@echo "  test-docker-enhanced    - Full test run with analysis (recommended)"
	@echo "  test-docker-headed      - Visual debugging with browser UI"
	@echo "  test-docker-debug       - Interactive debug shell"
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

# Backward compatibility aliases
docker-dev-up: docker-up
docker-dev-down: docker-down
docker-dev-build: docker-build
docker-dev-logs: docker-logs
docker-dev-https: docker-https
dev-cert: cert
dev-reset: db-reset
dev-fresh: db-fresh
dev-backup: db-backup
dev-shell-db: db-shell
dev-logs-db: db-logs
dev-status: db-status

# =============================================================================
# CIELO WEBSITE PLAYWRIGHT TESTING
# =============================================================================

# Check if services are running
_check-services:
	@echo "Checking if services are running..."
	@docker compose ps | grep -q "Up" || { echo "Services not running. Starting services..."; docker compose up -d; sleep 20; }
	@echo "Services are running"

# Run all CIELO website tests
test-cielo: _check-services
	@echo "Running all CIELO website tests..."
	@echo "==============================================="
	@echo "This includes:"
	@echo "  - CIELO smoke tests (homepage, auth flow)"
	@echo "  - Azure Costs integration tests"
	@echo "  - Billing API integration tests"
	@echo "  - Cross-service authentication tests"
	@echo "==============================================="
	@$(MAKE) test-cielo-smoke
	@$(MAKE) test-cielo-integration
	@echo ""
	@echo "All CIELO tests completed!"

# Run CIELO smoke tests only
test-cielo-smoke: _check-services
	@echo "Running CIELO smoke tests..."
	@echo "Testing: Homepage, authentication flow, responsive design"
	cd playwright/cielo-website/smoke-tests && python test_cielo_index.py
	cd playwright/cielo-website/smoke-tests && python test_cielo_auth_flow.py
	@echo "CIELO smoke tests completed!"

# Run CIELO integration tests only
test-cielo-integration: _check-services
	@echo "Running CIELO integration tests..."
	@echo "Testing: Cross-service authentication to Azure Costs and Billing APIs"
	cd playwright/cielo-website/integration-tests && python test_azure_costs_access.py
	cd playwright/cielo-website/integration-tests && python test_billing_access.py
	@echo "CIELO integration tests completed!"

# Test Azure Costs cross-service authentication specifically
test-azure-costs: _check-services
	@echo "Testing Azure Costs API cross-service authentication..."
	@echo "Login via CIELO -> Access Azure Costs API -> Verify RBAC roles"
	cd playwright/cielo-website/integration-tests && python test_azure_costs_access.py
	@echo "Azure Costs authentication test completed!"

# Test Billing API cross-service authentication specifically
test-billing: _check-services
	@echo "Testing Billing API cross-service authentication..."
	@echo "Login via CIELO -> Access Billing API -> Verify authentication"
	cd playwright/cielo-website/integration-tests && python test_billing_access.py
	@echo "Billing API authentication test completed!"

# Test all cross-service authentication
test-cross-service: _check-services
	@echo "Testing comprehensive cross-service authentication..."
	@echo "Single login -> Multiple service access -> Security validation"
	cd playwright/cielo-website/integration-tests && python test_all_services.py
	@echo "Cross-service authentication test completed!"

# Run all CIELO tests (alias for test-cielo)
test-cielo-all: test-cielo

# Run Identity Provider admin API tests
test-identity-admin: _check-services
	@echo "Running Identity Provider Admin API tests..."
	@echo "==============================================="
	@echo "This includes:"
	@echo "  - User management API tests"
	@echo "  - Role management API tests"
	@echo "  - Bulk operations tests"
	@echo "  - Integration and cache tests"
	@echo "==============================================="
	@echo "Setting up test environment..."
	@docker compose exec identity-provider python manage.py migrate > /dev/null 2>&1 || true
	@docker compose exec identity-provider python manage.py setup_admin_test_user > /dev/null 2>&1 || true
	cd playwright/identity-provider/smoke-tests && python -m pytest -v
	@echo ""
	@echo "Identity Provider Admin API tests completed!"

# Run specific Identity Provider admin test suite
test-identity-admin-users: _check-services
	@echo "Running Identity Provider Admin API user management tests..."
	cd playwright/identity-provider/smoke-tests && python -m pytest test_admin_api_users.py -v
	@echo "User management tests completed!"

test-identity-admin-roles: _check-services
	@echo "Running Identity Provider Admin API role management tests..."
	cd playwright/identity-provider/smoke-tests && python -m pytest test_admin_api_roles.py -v
	@echo "Role management tests completed!"

test-identity-admin-bulk: _check-services
	@echo "Running Identity Provider Admin API bulk operations tests..."
	cd playwright/identity-provider/smoke-tests && python -m pytest test_admin_api_bulk.py -v
	@echo "Bulk operations tests completed!"

test-identity-admin-integration: _check-services
	@echo "Running Identity Provider Admin API integration tests..."
	cd playwright/identity-provider/smoke-tests && python -m pytest test_admin_api_integration.py -v
	@echo "Integration tests completed!"

# Show CIELO testing help
test-cielo-help:
	@echo "CIELO Website Testing Commands"
	@echo "=================================="
	@echo ""
	@echo "Quick Tests:"
	@echo "  test-cielo-smoke        - Homepage + auth flow (~2 min)"
	@echo "  test-azure-costs        - Azure Costs cross-service auth (~1 min)"
	@echo "  test-billing            - Billing API cross-service auth (~1 min)"
	@echo ""
	@echo "Integration Tests:"
	@echo "  test-cielo-integration  - All cross-service auth tests (~3 min)"
	@echo "  test-cross-service      - Comprehensive multi-service test (~2 min)"
	@echo ""
	@echo "Complete Testing:"
	@echo "  test-cielo             - All CIELO tests (~5 min)"
	@echo "  test-cielo-all         - Same as test-cielo"
	@echo ""
	@echo "What gets tested:"
	@echo "  * CIELO website functionality (login/logout/responsive design)"
	@echo "  * JWT authentication and cookie sharing"
	@echo "  * Cross-service authentication (CIELO -> Azure Costs)"
	@echo "  * Cross-service authentication (CIELO -> Billing API)"
	@echo "  * RBAC role validation and permissions"
	@echo "  * Security controls (unauthenticated access blocked)"
	@echo ""
	@echo "Test User: alice (password: password123)"
	@echo "Test Domain: cielo.viloforge.com"
	@echo ""
	@echo "Test Files Location:"
	@echo "  playwright/cielo-website/smoke-tests/"
	@echo "  playwright/cielo-website/integration-tests/"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - Docker services running (make docker-up)"
	@echo "  - Python 3.12+ with Playwright installed"
	@echo "  - Services: identity-provider, cielo-website, azure-costs, billing-api"
	@echo ""
	@echo "Troubleshooting:"
	@echo "  - Check services: docker compose ps"
	@echo "  - View logs: docker compose logs <service-name>"
	@echo "  - Restart services: make docker-down && make docker-up"
	@echo "  - Fresh start: make fresh-start"

# Install CIELO test dependencies
test-cielo-setup:
	@echo "Setting up CIELO test environment..."
	@echo "Installing Python dependencies for Playwright tests..."
	@python -m pip install playwright pytest requests
	@playwright install chromium
	@echo "CIELO test environment setup completed!"
	@echo "Run 'make test-cielo' to execute all tests"

# Check CIELO test status
test-cielo-status:
	@echo "CIELO Test Environment Status"
	@echo "================================"
	@echo ""
	@echo "Docker Services:"
	@docker compose ps | grep -E "(identity-provider|cielo-website|azure-costs|billing-api)" || echo "Required services not running"
	@echo ""
	@echo "Service Health Checks:"
	@echo "CIELO Website:"
	@curl -s -k https://cielo.viloforge.com/accounts/login/ > /dev/null && echo "  CIELO website accessible" || echo "  CIELO website not accessible"
	@echo "Azure Costs API:"
	@curl -s -k https://azure-costs.cielo.viloforge.com/api/health > /dev/null && echo "  Azure Costs API accessible" || echo "  Azure Costs API not accessible"
	@echo "Billing API:"
	@curl -s -k https://billing.vfservices.viloforge.com/health > /dev/null && echo "  Billing API accessible" || echo "  Billing API not accessible"
	@echo ""
	@echo "Python Environment:"
	@python --version 2>/dev/null && echo "  Python available" || echo "  Python not available"
	@python -c "import playwright; print('  Playwright installed')" 2>/dev/null || echo "  Playwright not installed (run: make test-cielo-setup)"
	@echo ""
	@echo "Test Files:"
	@ls -la playwright/cielo-website/smoke-tests/*.py 2>/dev/null | wc -l | xargs -I {} echo "  Smoke tests: {} files"
	@ls -la playwright/cielo-website/integration-tests/*.py 2>/dev/null | wc -l | xargs -I {} echo "  Integration tests: {} files"

.DEFAULT_GOAL := help