# vfservices

This repository contains a multi-project Django monorepo used for experimenting
with JWT-based SSO across several services. The projects included are:

- `identity-provider` – central login and token issuance with RBAC/ABAC management
- `website` – primary frontend website
- `billing-api` – example API service
- `inventory-api` – cloud resources inventory service

## Key Features

- **JWT-based SSO**: Shared authentication across all services via `common/jwt_auth`
- **RBAC/ABAC Authorization**: Fine-grained permissions combining roles and attributes via `common/rbac_abac`
- **Redis Caching**: High-performance attribute storage with real-time updates
- **Service Autonomy**: Each service manages its own authorization policies
- **Django Integration**: Seamless integration with Django models and DRF

## Testing

This project includes comprehensive end-to-end testing using Playwright. Tests cover all services through the Traefik reverse proxy setup.

### Quick Test Commands

```bash
# Setup and run all tests
make test

# Interactive test development
make test-ui

# Visual debugging
make test-headed

# Docker-based testing
make test-docker
```

See the [Testing Documentation](tests/README.md) for detailed information.

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
export BASE_DOMAIN="vlservices.viloforge.com"  # optional override
make dev-cert   # obtains certificates for *.vlservices.viloforge.com
```

Once certificates exist you can start all services at once:

```bash
make up
```

Prior versions of the repository used SQLite databases that the Makefile
initialised automatically. The stack now relies on a shared PostgreSQL
container so no local database files are created. Migrations are applied
automatically at container start up by each project's `entrypoint.sh`.

Ensure your hosts file resolves the development subdomains to localhost:

```
127.0.0.1 login.vlservices.viloforge.com
127.0.0.1 website.vlservices.viloforge.com
127.0.0.1 billing-api.vlservices.viloforge.com
127.0.0.1 inventory-api.vlservices.viloforge.com
```

## Docker-based Development

You can also run the projects using Docker. Each project includes a `Dockerfile` and the main compose file `docker-compose.yml` starts them together with [Traefik](https://traefik.io) for routing, **a PostgreSQL container** for data storage, and **Redis** for RBAC/ABAC attribute caching. Services run on plain HTTP and are reloaded whenever code changes because the project directories are mounted as bind volumes.

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

The compose file also starts a `postgres` container. Each Django service is
configured via environment variables (`POSTGRES_HOST`, `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD`) to connect to this database and runs
migrations on start up.

Then open `http://website.vfservices.viloforge.com` in your browser.

The identity provider automatically creates a default administrative user named
`admin` with password `admin123` the first time it starts if the user does not
already exist. Use these credentials to sign into the Django admin or login
page during development.

## RBAC/ABAC Authorization System

The project includes a comprehensive Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC) system. Key features:

- **Policy-based Authorization**: Define reusable authorization rules using decorators
- **Model Integration**: Add authorization to Django models with `ABACModelMixin`
- **Efficient Filtering**: Database-level permission filtering for QuerySets
- **DRF Support**: Drop-in permission classes for REST APIs
- **Redis Caching**: Sub-millisecond permission lookups with automatic invalidation

See the [RBAC-ABAC Documentation](docs/RBAC-ABAC-IMPLEMENTATION.md) for detailed information and the [Implementation Plan](docs/PLAN-RBAC-ABAC-Implementation.md) for the current status.

### Demo Users

The system includes four pre-configured demo users that showcase different access patterns:
- **Alice**: Senior Manager with cross-functional access
- **Bob**: Billing Specialist focused on finance operations  
- **Charlie**: Cloud Infrastructure Manager with resource management
- **David**: Customer Service Representative with read-only access

See the [RBAC-ABAC Demo Users Guide](docs/RBAC-ABAC-DEMO-USERS.md) for implementation details and test scenarios.

### Interactive Demo Pages

The website service includes comprehensive demo pages for exploring and testing the RBAC-ABAC system:

- **Demo Dashboard** (`/demo/`): Main hub for accessing all demo features and checking system setup status
- **RBAC Dashboard** (`/demo/rbac/`): View and compare user permissions across services
- **API Explorer** (`/demo/api/`): Test API endpoints with different user permissions interactively
- **Permission Matrix** (`/demo/matrix/`): Visual grid showing all roles and user assignments
- **Access Playground** (`/demo/playground/`): Pre-configured scenarios demonstrating access patterns

Access these pages after logging into the website service at `http://website.vfservices.viloforge.com/demo/`

### Demo Setup Commands

```bash
# Complete demo setup (creates users, assigns roles, sets attributes)
make demo-setup

# Refresh Redis cache for all demo users
python manage.py refresh_demo_cache

# Setup demo users only
python manage.py setup_demo_users

# Complete the full demo setup
python manage.py complete_demo_setup
```

