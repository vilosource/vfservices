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

The servers run with `runserver_plus` from **django-extensions** to enable
HTTPS in development. This package is installed from `requirements.txt`, and
each project includes `django_extensions` in `INSTALLED_APPS`.

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

The Makefile will automatically create the local SQLite databases for each
project on first run by executing `python manage.py migrate` when the database
file is missing. Subsequent runs will skip this step.

Ensure your hosts file resolves the development subdomains to localhost:

```
127.0.0.1 login.vlservices.viloforge.com
127.0.0.1 website.vlservices.viloforge.com
127.0.0.1 billing-api.vlservices.viloforge.com
127.0.0.1 inventory-api.vlservices.viloforge.com
```

## Docker-based Development

You can also run the projects using Docker. Each project includes a `Dockerfile` and the main compose file `docker-compose.yml` starts them together with [Traefik](https://traefik.io) for routing. Services run on plain HTTP and are reloaded whenever code changes because the project directories are mounted as bind volumes.

Start the stack with:

```bash
docker compose up --build
```

Traefik listens on port 80 and routes based on subdomain. Ensure your hosts file maps the development domain to `localhost`, for example:

```text
127.0.0.1 login.vfservices.viloforge.com
127.0.0.1 website.vfservices.viloforge.com
127.0.0.1 billing-api.vfservices.viloforge.com
127.0.0.1 inventory-api.vfservices.viloforge.com
```

Then open `http://website.vfservices.viloforge.com` in your browser.

The identity provider automatically creates a default administrative user named
`admin` with password `admin` the first time it starts if the user does not
already exist. Use these credentials to sign into the Django admin or login
page during development.

