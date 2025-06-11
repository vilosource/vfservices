# Let's Encrypt Certificates

This project uses real HTTPS certificates from Let's Encrypt when running the development servers. Certificates are obtained using Certbot with the Cloudflare DNS challenge.

## Obtaining Certificates

Run the following command once you have the required environment variables set:

```bash
make dev-cert
```

This runs `scripts/get_dev_certs.sh`, which in turn executes Certbot in a Docker container defined in `docker-compose.yml`.

### Required Environment Variables

- `CLOUDFLARE_API_TOKEN` – API token with permission to modify DNS records for the development domain.
- `LETSENCRYPT_EMAIL` – email address used when requesting certificates.
- `DEV_DOMAIN` – base domain for development (defaults to `vlservices.viloforge.com`).

The generated certificates are stored under `certs/live/<DEV_DOMAIN>/` as `fullchain.pem` and `privkey.pem`.

## Using Certificates

The Makefile passes the certificate and key to each Django project's `runserver_plus` command using the `--cert-file` and `--key-file` options. When running `make up`, each service starts with HTTPS enabled using the files from the `certs` directory.

Ensure the certificates exist before running the servers.
