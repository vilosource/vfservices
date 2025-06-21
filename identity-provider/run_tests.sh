#!/bin/bash

# Identity Provider API Test Runner Script

echo "=========================================="
echo "Identity Provider API Tests"
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default to running all tests
TEST_TARGET=${1:-"identity_app.tests"}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found. Please run this script from the identity-provider directory.${NC}"
    exit 1
fi

# Function to run tests
run_tests() {
    echo -e "${YELLOW}Running tests: $1${NC}"
    python manage.py test $1 --verbosity=2
    return $?
}

# Main execution
case "$1" in
    "api")
        echo "Running API endpoint tests..."
        run_tests "identity_app.tests.test_api_endpoints"
        ;;
    "admin")
        echo "Running admin API tests..."
        run_tests "identity_app.tests.test_admin_api_complete"
        ;;
    "all")
        echo "Running all tests..."
        run_tests "identity_app.tests"
        ;;
    "coverage")
        echo "Running tests with coverage..."
        coverage run --source='identity_app' manage.py test identity_app.tests
        coverage report
        echo -e "${GREEN}HTML coverage report will be generated in htmlcov/${NC}"
        coverage html
        ;;
    "quick")
        echo "Running quick smoke tests..."
        # Run a subset of critical tests
        python manage.py test \
            identity_app.tests.test_api_endpoints.LoginAPITestCase \
            identity_app.tests.test_admin_api_complete.UserViewSetTestCase.test_list_users \
            --verbosity=1
        ;;
    *)
        # Run specific test or all tests
        if [ -z "$1" ]; then
            echo "Running all tests (use './run_tests.sh -h' for options)..."
            run_tests "identity_app.tests"
        else
            run_tests "$1"
        fi
        ;;
esac

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed successfully!${NC}"
else
    echo -e "${RED}✗ Tests failed!${NC}"
    exit 1
fi

# Show help if requested
if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo ""
    echo "Usage: ./run_tests.sh [option]"
    echo ""
    echo "Options:"
    echo "  api       - Run only API endpoint tests"
    echo "  admin     - Run only admin API tests"
    echo "  all       - Run all tests"
    echo "  coverage  - Run tests with coverage report"
    echo "  quick     - Run quick smoke tests"
    echo "  <target>  - Run specific test (e.g., identity_app.tests.test_api_endpoints.LoginAPITestCase)"
    echo "  -h        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh"
    echo "  ./run_tests.sh api"
    echo "  ./run_tests.sh coverage"
    echo "  ./run_tests.sh identity_app.tests.test_api_endpoints.LoginAPITestCase.test_login_success"
fi