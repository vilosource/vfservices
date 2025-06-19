#!/bin/bash
# Script to generate test environment file from template
# Usage: ./scripts/generate_test_env.sh [BASE_DOMAIN]

# Get BASE_DOMAIN from argument or environment, default to vfservices.viloforge.com
if [ -n "$1" ]; then
    export BASE_DOMAIN="$1"
else
    export BASE_DOMAIN=${BASE_DOMAIN:-vfservices.viloforge.com}
fi

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Check if template exists
if [ ! -f "$PROJECT_ROOT/tests/.env.template" ]; then
    echo "Error: tests/.env.template not found!"
    exit 1
fi

# Generate .env file from template
echo "Generating test environment file for domain: $BASE_DOMAIN"
envsubst < "$PROJECT_ROOT/tests/.env.template" > "$PROJECT_ROOT/tests/.env"

if [ $? -eq 0 ]; then
    echo "Successfully generated tests/.env with BASE_DOMAIN=$BASE_DOMAIN"
    echo ""
    echo "Service URLs configured:"
    echo "  - Identity: https://identity.$BASE_DOMAIN"
    echo "  - Website: https://website.$BASE_DOMAIN"
    echo "  - Billing: https://billing.$BASE_DOMAIN"
    echo "  - Inventory: https://inventory.$BASE_DOMAIN"
else
    echo "Error: Failed to generate tests/.env"
    exit 1
fi