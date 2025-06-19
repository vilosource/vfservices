"""
Management command to register CIELO service with the Identity Provider.
This sends the service manifest to create roles and attributes.
"""
import requests
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from webapp.manifest import SERVICE_MANIFEST


class Command(BaseCommand):
    help = 'Register CIELO Website service with the Identity Provider'

    def add_arguments(self, parser):
        parser.add_argument(
            '--identity-url',
            default='http://identity-provider:8000',
            help='Identity Provider URL (default: http://identity-provider:8000)'
        )

    def handle(self, *args, **options):
        identity_url = options['identity_url']
        
        # Use the identity provider URL from settings if available
        if hasattr(settings, 'IDENTITY_PROVIDER_URL'):
            identity_url = settings.IDENTITY_PROVIDER_URL
            
        register_url = f"{identity_url}/api/services/register/"
        
        self.stdout.write(f"Registering CIELO service with Identity Provider at {register_url}")
        
        try:
            # Send the manifest to the identity provider
            response = requests.post(
                register_url,
                json=SERVICE_MANIFEST,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully registered service: {result.get('service', 'Unknown')}"
                    )
                )
                
                # Display version info
                version = result.get('version', 'Unknown')
                registered_at = result.get('registered_at', 'Unknown')
                is_active = result.get('is_active', False)
                
                self.stdout.write(f"  Version: {version}")
                self.stdout.write(f"  Registered at: {registered_at}")
                self.stdout.write(f"  Active: {is_active}")
                
                # Display manifest info from what we sent
                self.stdout.write("\nRegistered roles:")
                for role in SERVICE_MANIFEST.get('roles', []):
                    self.stdout.write(f"  - {role['name']}: {role['display_name']}")
                
                self.stdout.write("\nRegistered attributes:")
                for attr in SERVICE_MANIFEST.get('attributes', []):
                    self.stdout.write(f"  - {attr['name']}: {attr['display_name']}")
                        
            elif response.status_code == 400:
                error_data = response.json()
                self.stdout.write(
                    self.style.WARNING(f"Service already registered or validation error: {error_data}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"Failed to register service. Status: {response.status_code}, "
                        f"Response: {response.text}"
                    )
                )
                
        except requests.exceptions.ConnectionError:
            self.stdout.write(
                self.style.ERROR(
                    f"Could not connect to Identity Provider at {identity_url}. "
                    "Make sure the Identity Provider service is running."
                )
            )
        except requests.exceptions.Timeout:
            self.stdout.write(
                self.style.ERROR("Request timed out. The Identity Provider may be overloaded.")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"An error occurred: {str(e)}")
            )