#!/bin/bash

# Azure Costs API Playwright Tests Runner Script
# This script helps run the Playwright tests with common configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
DEFAULT_BASE_URL="https://azure-costs.cielo.viloforge.com"
DEFAULT_IDP_URL="https://identity.cielo.viloforge.com"

# Function to print colored output
print_color() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if service is accessible
check_service() {
    url=$1
    service_name=$2
    
    print_color "$YELLOW" "Checking $service_name at $url..."
    
    if curl -s -o /dev/null -w "%{http_code}" "$url/api/health" | grep -q "200\|404"; then
        print_color "$GREEN" "✓ $service_name is accessible"
        return 0
    else
        print_color "$RED" "✗ $service_name is not accessible at $url"
        return 1
    fi
}

# Display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -H, --headed            Run tests in headed mode (show browser)"
    echo "  -s, --slow              Run tests with slow motion (1 second delay)"
    echo "  -v, --video             Record videos of test execution"
    echo "  -f, --file FILE         Run specific test file"
    echo "  -t, --test TEST         Run specific test"
    echo "  -m, --marker MARKER     Run tests with specific marker (api, browser, auth)"
    echo "  --setup                 Install dependencies and Playwright browsers"
    echo "  --check                 Check if services are accessible"
    echo ""
    echo "Environment variables:"
    echo "  AZURE_COSTS_BASE_URL    Azure Costs API URL (default: $DEFAULT_BASE_URL)"
    echo "  IDENTITY_PROVIDER_URL   Identity Provider URL (default: $DEFAULT_IDP_URL)"
    echo "  TEST_USERNAME          Test username"
    echo "  TEST_PASSWORD          Test password"
    echo ""
    echo "Examples:"
    echo "  $0                     # Run all tests in headless mode"
    echo "  $0 -H                  # Run tests with browser visible"
    echo "  $0 -f test_azure_costs_api.py  # Run specific test file"
    echo "  $0 -m api              # Run only API tests"
    echo "  $0 --check             # Check service availability"
    echo "  $0 --setup             # Install dependencies"
}

# Parse command line arguments
HEADLESS=true
SLOW_MO=0
RECORD_VIDEO=false
TEST_FILE=""
TEST_NAME=""
MARKER=""
SETUP=false
CHECK_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -H|--headed)
            HEADLESS=false
            shift
            ;;
        -s|--slow)
            SLOW_MO=1000
            shift
            ;;
        -v|--video)
            RECORD_VIDEO=true
            shift
            ;;
        -f|--file)
            TEST_FILE="$2"
            shift 2
            ;;
        -t|--test)
            TEST_NAME="$2"
            shift 2
            ;;
        -m|--marker)
            MARKER="$2"
            shift 2
            ;;
        --setup)
            SETUP=true
            shift
            ;;
        --check)
            CHECK_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Setup environment if requested
if [ "$SETUP" = true ]; then
    print_color "$YELLOW" "Setting up test environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_color "$YELLOW" "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_color "$YELLOW" "Installing dependencies..."
    pip install -r requirements.txt
    
    # Install Playwright browsers
    print_color "$YELLOW" "Installing Playwright browsers..."
    playwright install chromium
    
    print_color "$GREEN" "✓ Setup complete!"
    exit 0
fi

# Set environment variables
export AZURE_COSTS_BASE_URL="${AZURE_COSTS_BASE_URL:-$DEFAULT_BASE_URL}"
export IDENTITY_PROVIDER_URL="${IDENTITY_PROVIDER_URL:-$DEFAULT_IDP_URL}"
export HEADLESS="$HEADLESS"
export SLOW_MO="$SLOW_MO"
export RECORD_VIDEO="$RECORD_VIDEO"
export IGNORE_HTTPS_ERRORS="${IGNORE_HTTPS_ERRORS:-true}"

# Check services if requested
if [ "$CHECK_ONLY" = true ]; then
    print_color "$YELLOW" "Checking service availability..."
    
    check_service "$AZURE_COSTS_BASE_URL" "Azure Costs API"
    azure_costs_status=$?
    
    check_service "$IDENTITY_PROVIDER_URL" "Identity Provider"
    idp_status=$?
    
    if [ $azure_costs_status -eq 0 ] && [ $idp_status -eq 0 ]; then
        print_color "$GREEN" "✓ All services are accessible!"
        exit 0
    else
        print_color "$RED" "✗ Some services are not accessible"
        exit 1
    fi
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_color "$RED" "Virtual environment not found. Run '$0 --setup' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Construct pytest command
PYTEST_CMD="pytest -v"

# Add test file if specified
if [ -n "$TEST_FILE" ]; then
    PYTEST_CMD="$PYTEST_CMD $TEST_FILE"
fi

# Add specific test if specified
if [ -n "$TEST_NAME" ]; then
    PYTEST_CMD="$PYTEST_CMD -k $TEST_NAME"
fi

# Add marker if specified
if [ -n "$MARKER" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKER"
fi

# Print test configuration
print_color "$YELLOW" "Test Configuration:"
echo "  Azure Costs API URL: $AZURE_COSTS_BASE_URL"
echo "  Identity Provider URL: $IDENTITY_PROVIDER_URL"
echo "  Headless: $HEADLESS"
echo "  Slow Motion: ${SLOW_MO}ms"
echo "  Record Video: $RECORD_VIDEO"
echo ""

# Check if credentials are set
if [ -z "$TEST_USERNAME" ] || [ -z "$TEST_PASSWORD" ]; then
    print_color "$YELLOW" "Warning: TEST_USERNAME or TEST_PASSWORD not set. Authentication tests may fail."
    echo ""
fi

# Run tests
print_color "$GREEN" "Running tests..."
echo "Command: $PYTEST_CMD"
echo ""

# Execute tests
$PYTEST_CMD

# Deactivate virtual environment
deactivate

print_color "$GREEN" "✓ Test execution complete!"