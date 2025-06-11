VF_JWT_SECRET ?= change-me
DEV_DOMAIN ?= vlservices.viloforge.com
CERT_DIR ?= certs/live/$(DEV_DOMAIN)
CERT_FILE ?= $(CERT_DIR)/fullchain.pem
KEY_FILE ?= $(CERT_DIR)/privkey.pem

.PHONY: up dev-cert

up:
$(MAKE) -j4 run-identity run-website run-billing run-inventory

run-identity:
VF_JWT_SECRET=$(VF_JWT_SECRET) \
SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
python identity-provider/manage.py runserver_plus 8001 \
    --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-website:
VF_JWT_SECRET=$(VF_JWT_SECRET) \
SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
python website/manage.py runserver_plus 8002 \
    --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-billing:
VF_JWT_SECRET=$(VF_JWT_SECRET) \
SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
python billing-api/manage.py runserver_plus 8003 \
    --cert-file $(CERT_FILE) --key-file $(KEY_FILE)

run-inventory:
VF_JWT_SECRET=$(VF_JWT_SECRET) \
SSO_COOKIE_DOMAIN=.${DEV_DOMAIN} \
python inventory-api/manage.py runserver_plus 8004 \
    --cert-file $(CERT_FILE) --key-file $(KEY_FILE)


device-cert:
@echo "Deprecated target name: use dev-cert"


dev-cert:
./scripts/get_dev_certs.sh
