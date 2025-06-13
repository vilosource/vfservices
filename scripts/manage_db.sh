#!/bin/bash
set -euo pipefail

COMPOSE_FILE="${1:-docker-compose.dev.yml}"

case "${2:-help}" in
    "reset")
        echo "Resetting all databases..."
        docker compose -f "$COMPOSE_FILE" down
        docker volume rm vfservices_pgdata 2>/dev/null || true
        echo "Databases reset. Start services to recreate."
        ;;
    "drop-all")
        echo "Dropping all application databases..."
        docker compose -f "$COMPOSE_FILE" exec postgres psql -U vfuser -d postgres -c "
        DROP DATABASE IF EXISTS vfdb_identity;
        DROP DATABASE IF EXISTS vfdb_website;
        DROP DATABASE IF EXISTS vfdb_billing;
        DROP DATABASE IF EXISTS vfdb_inventory;
        "
        echo "All databases dropped."
        ;;
    "list")
        echo "Listing databases..."
        docker compose -f "$COMPOSE_FILE" exec postgres psql -U vfuser -d postgres -c "\l"
        ;;
    "shell")
        echo "Opening PostgreSQL shell..."
        docker compose -f "$COMPOSE_FILE" exec postgres psql -U vfuser -d postgres
        ;;
    "backup")
        BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        echo "Backing up databases to $BACKUP_DIR..."
        for db in vfdb_identity vfdb_website vfdb_billing vfdb_inventory; do
            echo "Backing up $db..."
            docker compose -f "$COMPOSE_FILE" exec postgres pg_dump -U vfuser "$db" > "$BACKUP_DIR/$db.sql" 2>/dev/null || echo "Database $db not found, skipping..."
        done
        echo "Backup completed in $BACKUP_DIR"
        ;;
    "restore")
        BACKUP_DIR="${3:-}"
        if [ -z "$BACKUP_DIR" ] || [ ! -d "$BACKUP_DIR" ]; then
            echo "Usage: $0 [compose-file] restore [backup-directory]"
            echo "Available backups:"
            ls -la ./backups/ 2>/dev/null || echo "No backups found"
            exit 1
        fi
        echo "Restoring databases from $BACKUP_DIR..."
        for db in vfdb_identity vfdb_website vfdb_billing vfdb_inventory; do
            if [ -f "$BACKUP_DIR/$db.sql" ]; then
                echo "Restoring $db..."
                docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U vfuser -d "$db" < "$BACKUP_DIR/$db.sql"
            else
                echo "Backup file $BACKUP_DIR/$db.sql not found, skipping..."
            fi
        done
        echo "Restore completed."
        ;;
    "status")
        echo "=== Database Status ==="
        docker compose -f "$COMPOSE_FILE" exec postgres psql -U vfuser -d postgres -c "
        SELECT datname as \"Database\", 
               pg_size_pretty(pg_database_size(datname)) as \"Size\",
               (SELECT count(*) FROM pg_stat_activity WHERE datname = pg_database.datname) as \"Connections\"
        FROM pg_database 
        WHERE datname LIKE 'vfdb_%' 
        ORDER BY datname;
        "
        ;;
    *)
        echo "Usage: $0 [compose-file] [command] [options]"
        echo ""
        echo "Compose files:"
        echo "  docker-compose.yml     - Production"
        echo "  docker-compose.dev.yml - Development (default)"
        echo ""
        echo "Commands:"
        echo "  reset      - Remove volume and reset all databases"
        echo "  drop-all   - Drop all application databases"
        echo "  list       - List all databases"
        echo "  shell      - Open PostgreSQL shell"
        echo "  backup     - Backup all databases to timestamped directory"
        echo "  restore    - Restore databases from backup directory"
        echo "  status     - Show database status and sizes"
        echo ""
        echo "Examples:"
        echo "  $0 docker-compose.dev.yml reset"
        echo "  $0 docker-compose.yml backup"
        echo "  $0 docker-compose.dev.yml restore ./backups/20240613_120000"
        ;;
esac
