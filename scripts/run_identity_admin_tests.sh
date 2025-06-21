#!/bin/bash
# Script to run Identity Provider admin API tests

echo "Setting up Identity Provider admin API tests..."
echo "============================================="

# Ensure migrations are applied
echo "Running Identity Provider migrations..."
docker compose exec identity-provider python manage.py migrate

# Create admin test user with identity_admin role
echo "Creating admin test user..."
docker compose exec identity-provider python manage.py setup_admin_test_user

# Check service status
echo ""
echo "Checking service status..."
curl -sk https://identity.vfservices.viloforge.com/api/status/ > /dev/null
if [ $? -eq 0 ]; then
    echo "✓ Identity Provider is accessible"
else
    echo "✗ Identity Provider is not accessible at https://identity.vfservices.viloforge.com"
    echo "Please ensure services are running: make docker-up"
    exit 1
fi

# Install test dependencies if needed
echo ""
echo "Checking test dependencies..."
python -c "import playwright" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Playwright..."
    pip install playwright pytest requests
    playwright install chromium
fi

# Run the tests
echo ""
echo "Running Identity Provider admin API tests..."
echo "============================================="
cd playwright/identity-provider/smoke-tests

if [ "$1" == "users" ]; then
    echo "Running user management tests only..."
    python -m pytest test_admin_api_users.py -v
elif [ "$1" == "roles" ]; then
    echo "Running role management tests only..."
    python -m pytest test_admin_api_roles.py -v
elif [ "$1" == "bulk" ]; then
    echo "Running bulk operations tests only..."
    python -m pytest test_admin_api_bulk.py -v
elif [ "$1" == "integration" ]; then
    echo "Running integration tests only..."
    python -m pytest test_admin_api_integration.py -v
else
    echo "Running all tests..."
    python -m pytest -v
fi

echo ""
echo "Test run complete!"