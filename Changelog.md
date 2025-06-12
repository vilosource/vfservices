# Changelog

## [Unreleased]
- Initial repository scaffolding with multiple Django projects: identity-provider, website, billing-api, inventory-api.
- Added shared JWT authentication utilities and middleware.
- Implemented demo website page and DRF health/private endpoints for each API.
- Added identity provider login/logout pages and login API.
- Added Makefile and dev certificate generation script.
- Replaced self-signed cert generation with Let's Encrypt via Docker Compose.
- Updated Makefile to run all Django projects with runserver_plus over HTTPS.
- Documented domain configuration and Cloudflare-based certificate flow.
- Fixed Makefile tab issues and added `LetsEncrypt.md` documentation.
- Added `django_extensions` to each project's `INSTALLED_APPS` so
  `runserver_plus` works correctly during development.
- Makefile now initializes SQLite databases automatically if they do not exist
  and sets `PYTHONPATH` so shared `common` modules import correctly.
- Added Dockerfiles for each project and docker-compose.dev.yml using Traefik for development.
- docker-compose.yml now starts all Django projects with Traefik and mounts the source
  directories so code changes reload immediately.
