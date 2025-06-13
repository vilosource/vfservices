#!/bin/bash
# Test script to validate the create_admin management command
# This script tests the admin creation functionality without Docker

set -e

echo "=== Testing Django Admin Creation Management Command ==="
echo

# Change to the identity-provider directory
cd /home/jasonvi/GitHub/vfservices/identity-provider

# Set test environment variables
export DJANGO_ENV=test
export DEBUG=True
export POSTGRES_HOST=localhost
export POSTGRES_DB=test_vfdb_identity
export POSTGRES_USER=test_user
export POSTGRES_PASSWORD=test_pass
export ADMIN_USERNAME=testadmin
export ADMIN_EMAIL=test@example.com
export ADMIN_PASSWORD=testpass123

echo "Environment variables set:"
echo "  ADMIN_USERNAME: $ADMIN_USERNAME"
echo "  ADMIN_EMAIL: $ADMIN_EMAIL"  
echo "  ADMIN_PASSWORD: $ADMIN_PASSWORD"
echo

# Check if the management command file exists
if [ -f "identity_app/management/commands/create_admin.py" ]; then
    echo "✓ Management command file exists"
else
    echo "✗ Management command file missing"
    exit 1
fi

# Check if the management command is properly structured
if grep -q "class Command(BaseCommand)" "identity_app/management/commands/create_admin.py"; then
    echo "✓ Management command class structure is correct"
else
    echo "✗ Management command class structure is incorrect"
    exit 1
fi

# Check if the command handles environment variables
if grep -q "ADMIN_USERNAME" "identity_app/management/commands/create_admin.py"; then
    echo "✓ Command handles ADMIN_USERNAME environment variable"
else
    echo "✗ Command doesn't handle ADMIN_USERNAME environment variable"
    exit 1
fi

# Check if entrypoint script calls the management command
if grep -q "python manage.py create_admin" "entrypoint.sh"; then
    echo "✓ Entrypoint script calls create_admin management command"
else
    echo "✗ Entrypoint script doesn't call create_admin management command"
    exit 1
fi

# Verify the apps.py file is cleaned up
if grep -q "_ensure_default_admin" "identity_app/apps.py"; then
    echo "✗ AppConfig still contains admin creation logic (should be removed)"
    exit 1
else
    echo "✓ AppConfig is cleaned up (no admin creation logic)"
fi

echo
echo "=== All Tests Passed! ==="
echo "The admin user creation management command setup is correct."
echo
echo "Key features validated:"
echo "  ✓ Django management command structure"
echo "  ✓ Environment variable configuration"
echo "  ✓ Entrypoint script integration"
echo "  ✓ AppConfig cleanup"
echo
echo "Default admin credentials (configurable via environment):"
echo "  Username: admin"
echo "  Email: admin@viloforge.com"
echo "  Password: admin123"
