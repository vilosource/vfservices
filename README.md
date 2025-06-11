# vfservices

This repository contains a multi-project Django monorepo used for experimenting
with JWT-based SSO across several services. The projects included are:

- `identity-provider` – central login and token issuance
- `website` – primary frontend website
- `billing-api` – example API service
- `inventory-api` – example API service

Shared JWT authentication utilities live under `common/jwt_auth` and are used by
each project via middleware.

## Running Locally

Create a Python virtual environment, install the dependencies from
`requirements.txt` and export a `VF_JWT_SECRET` environment variable:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export VF_JWT_SECRET="super-secret-key"
```

You can start all services at once using the provided Makefile:

```bash
make dev-cert   # generates self-signed certificates
make up         # runs all projects on different ports
```
