#!/bin/bash
# This script runs in the background to complete demo setup after services have started

# Wait 30 seconds for other services to start and register
sleep 30

echo "Running delayed demo setup completion..."
cd /code/identity-provider

# Try to complete the demo setup
python manage.py complete_demo_setup --wait 60 --interval 5

echo "Delayed demo setup completed"