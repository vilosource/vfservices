# Database Management Guide

This guide covers the database management tools and workflows for the VFServices microservices project.

## Quick Reference

### Development Workflow Commands

```bash
# Fresh start (reset everything)
make dev-fresh

# Reset databases only
make dev-reset

# Backup databases before changes
make dev-backup

# Check environment status
make dev-status

# Open database shell
make dev-shell-db

# Restart individual services
make restart-identity
make restart-website
make restart-billing
make restart-inventory
```

## Database Architecture

Each Django microservice has its own dedicated PostgreSQL database:

- **identity-provider** → `vfdb_identity`
- **website** → `vfdb_website`
- **billing-api** → `vfdb_billing`
- **inventory-api** → `vfdb_inventory`

All databases run on a single PostgreSQL instance with superuser `vfuser`.

## Database Management Script

The `scripts/manage_db.sh` script provides comprehensive database management:

```bash
# Usage: ./scripts/manage_db.sh [compose-file] [command] [options]

# Reset all databases (removes volume)
./scripts/manage_db.sh docker-compose.dev.yml reset

# Drop application databases (keep PostgreSQL running)
./scripts/manage_db.sh docker-compose.dev.yml drop-all

# List all databases
./scripts/manage_db.sh docker-compose.dev.yml list

# Open PostgreSQL shell
./scripts/manage_db.sh docker-compose.dev.yml shell

# Backup databases
./scripts/manage_db.sh docker-compose.dev.yml backup

# Restore from backup
./scripts/manage_db.sh docker-compose.dev.yml restore ./backups/20240613_120000

# Show database status and sizes
./scripts/manage_db.sh docker-compose.dev.yml status
```

## Development Environment

### Environment Variables

Development services automatically get these environment variables:

- `DJANGO_ENV=development` - Enables development features
- `DEBUG=True` - Django debug mode
- Database connection settings for PostgreSQL

### Automatic Features in Development

When `DJANGO_ENV=development` is set:

1. **Fixtures Loading**: Automatically loads `fixtures/dev_data.json` if it exists
2. **Admin User Creation**: Creates admin user (username: admin, password: admin123) for identity-provider
3. **Debug Mode**: Enables Django debug features

### Database Initialization

Each service's entrypoint script automatically:

1. Waits for PostgreSQL to be ready
2. Checks if its database exists
3. Creates the database if it doesn't exist
4. Runs Django migrations
5. Creates/updates admin user using Django management command (identity-provider only)
6. Loads development fixtures (if in development mode)
7. Starts the Django application

### Admin User Management

The identity-provider service uses a Django management command to create and manage the admin user:

**Management Command**: `python manage.py create_admin`

This command:
- Checks if the admin user exists
- Creates a new admin user if it doesn't exist
- Updates the existing admin user's password and settings if it does exist
- Verifies password functionality after creation/update

**Environment Configuration**:
- `ADMIN_USERNAME` (default: `admin`)
- `ADMIN_EMAIL` (default: `admin@viloforge.com`)
- `ADMIN_PASSWORD` (default: `admin123`)

This approach is more reliable than creating users in Django's AppConfig.ready() method because:
- It runs after database migrations are complete
- It's executed in the correct process context
- It provides better error handling and logging
- It can be run independently for troubleshooting

## Backup and Restore

### Automatic Backups

```bash
# Backup development databases
make dev-backup

# Backup production databases
make prod-backup
```

Backups are stored in `./backups/YYYYMMDD_HHMMSS/` with separate SQL files for each database.

### Manual Restore

```bash
# Restore production databases
make prod-restore
# (will prompt for backup directory)

# Restore development databases
./scripts/manage_db.sh docker-compose.dev.yml restore ./backups/20240613_120000
```

## Troubleshooting

### Database Connection Issues

1. Check PostgreSQL is running:
   ```bash
   docker compose -f docker-compose.dev.yml ps postgres
   ```

2. Check database status:
   ```bash
   make dev-status
   ```

3. View PostgreSQL logs:
   ```bash
   make dev-logs-db
   ```

### Reset Everything

If you encounter persistent issues:

```bash
# Complete fresh start
make dev-fresh
```

This will:
1. Stop all containers
2. Remove the PostgreSQL volume
3. Rebuild all containers
4. Start services (databases will be recreated)

### Individual Service Issues

Restart specific services without affecting others:

```bash
make restart-identity    # Restart identity-provider
make restart-website     # Restart website
make restart-billing     # Restart billing-api
make restart-inventory   # Restart inventory-api
```

## Production Considerations

### Database Isolation

Each microservice uses its own database, providing:
- **Data isolation** between services
- **Independent scaling** and optimization
- **Separate backup/restore** capabilities
- **Independent schema evolution**

### Security

- Use strong passwords in production (set via environment variables)
- Consider using separate database users for each service
- Enable SSL for database connections in production
- Regular backup verification and testing

### Monitoring

Monitor database usage with:

```bash
# Check database sizes and connections
./scripts/manage_db.sh docker-compose.yml status
```

## Adding New Services

When adding a new Django microservice:

1. **Update docker-compose.yml**: Add database environment variables
2. **Create entrypoint.sh**: Use existing entrypoints as template
3. **Update manage_db.sh**: Add new database to backup/restore lists
4. **Add Makefile targets**: Add restart target for new service

Example environment variables for new service:
```yaml
environment:
  - POSTGRES_HOST=postgres
  - POSTGRES_DB=vfdb_newservice
  - POSTGRES_USER=${POSTGRES_USER:-vfuser}
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-vfpass}
```
