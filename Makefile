VF_JWT_SECRET ?= change-me

.PHONY: up dev-cert

up:
$(MAKE) -j4 run-identity run-website run-billing run-inventory

run-identity:
VF_JWT_SECRET=$(VF_JWT_SECRET) python identity-provider/manage.py runserver 8001

run-website:
VF_JWT_SECRET=$(VF_JWT_SECRET) python website/manage.py runserver 8002

run-billing:
VF_JWT_SECRET=$(VF_JWT_SECRET) python billing-api/manage.py runserver 8003

run-inventory:
VF_JWT_SECRET=$(VF_JWT_SECRET) python inventory-api/manage.py runserver 8004


device-cert:
@echo "Deprecated target name: use dev-cert"


dev-cert:
./scripts/get_dev_certs.sh
