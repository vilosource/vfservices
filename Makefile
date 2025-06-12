VF_JWT_SECRET ?= change-me
DEV_DOMAIN ?= vfservices.viloforge.com
CERT_DIR ?= certs/live/$(DEV_DOMAIN)
CERT_FILE ?= $(CERT_DIR)/fullchain.pem
KEY_FILE ?= $(CERT_DIR)/privkey.pem

.PHONY: up dev-cert

up:
	$(MAKE) -j4 run-identity run-website run-billing run-inventory

run-identity:
	if [ ! -f identity-provider/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python identity-provider/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python identity-provider/manage.py runserver_plus 8001 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-website:
	if [ ! -f website/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python website/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python website/manage.py runserver_plus 8002 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-billing:
	if [ ! -f billing-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python billing-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python billing-api/manage.py runserver_plus 8003 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-inventory:
	if [ ! -f inventory-api/db.sqlite3 ]; then \
	       PYTHONPATH=$(PWD) python inventory-api/manage.py migrate --noinput; \
	fi; \
	VF_JWT_SECRET=$(VF_JWT_SECRET) \
	SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
	PYTHONPATH=$(PWD) python inventory-api/manage.py runserver_plus 8004 \
	   --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

device-cert:
	@echo "Deprecated target name: use dev-cert"

dev-cert:
	./scripts/get_dev_certs.sh
