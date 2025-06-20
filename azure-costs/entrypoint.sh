#!/bin/sh
set -e

echo "Starting azure-costs entrypoint..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL at $POSTGRES_HOST..."
while ! nc -z "$POSTGRES_HOST" 5432; do
    echo "PostgreSQL is unavailable - sleeping"
    sleep 1
done
echo "PostgreSQL is up - continuing..."

# Check if database exists and create if needed
python3 << EOF
import os
import psycopg2
from psycopg2 import sql

db_name = os.environ["POSTGRES_DB"]
db_user = os.environ["POSTGRES_USER"]
db_password = os.environ["POSTGRES_PASSWORD"]
db_host = os.environ["POSTGRES_HOST"]
db_port = os.environ.get("POSTGRES_PORT", "5432")

def db_exists():
    try:
        conn = psycopg2.connect(
            dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port
        )
        conn.close()
        print(f"Database {db_name} exists.")
        return True
    except psycopg2.OperationalError:
        return False

if not db_exists():
    print(f"Database {db_name} does not exist. Creating...")
    conn = psycopg2.connect(
        dbname="postgres", user=db_user, password=db_password, host=db_host, port=db_port
    )
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
    cur.close()
    conn.close()
    print(f"Database {db_name} created.")
else:
    print(f"Database {db_name} already exists.")
EOF

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Execute the main command
echo "Starting Django application..."
exec "$@"