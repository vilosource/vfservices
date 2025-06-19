#!/bin/bash
# Script to complete demo user setup once all services are registered
# This can be run as a cron job or manually after all services are up

cd /code/identity-provider

# Wait up to 5 minutes for all services to register, checking every 10 seconds
echo "Attempting to complete demo user setup..."
python manage.py complete_demo_setup --wait 300 --interval 10

# Exit with the status of the command
exit $?