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

Before running the servers you will need valid HTTPS certificates. These are
retrieved from Let's Encrypt using a Dockerized Certbot image. Provide your
Cloudflare API token and email via environment variables and run
`make dev-cert` (see `LetsEncrypt.md` for details):

```bash
export CLOUDFLARE_API_TOKEN="<token>"
export LETSENCRYPT_EMAIL="you@example.com"
export DEV_DOMAIN="vlservices.viloforge.com"  # optional override
make dev-cert   # obtains certificates for *.vlservices.viloforge.com
```

Once certificates exist you can start all services at once:

```bash
make up
```

Ensure your hosts file resolves the development subdomains to localhost:

```
127.0.0.1 login.vlservices.viloforge.com
127.0.0.1 website.vlservices.viloforge.com
127.0.0.1 billing-api.vlservices.viloforge.com
127.0.0.1 inventory-api.vlservices.viloforge.com
```
