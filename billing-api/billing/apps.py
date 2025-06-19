from django.apps import AppConfig
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "billing"
    
    def ready(self):
        """Called when Django starts. Register our service manifest and policies."""
        # Import policies to register them
        try:
            from . import policies
            logger.info("Billing ABAC policies registered successfully")
        except Exception as e:
            logger.error(f"Failed to register billing policies: {e}")
        
        # Register manifest with Identity Provider
        # Always register in development to support testing
        self._register_manifest()
    
    def _register_manifest(self):
        """Register our service manifest with the Identity Provider."""
        try:
            from .manifest import BILLING_SERVICE_MANIFEST
            
            # In production, this would be the Identity Provider's internal URL
            identity_provider_url = "http://identity-provider:8000/api/services/register/"
            
            response = requests.post(
                identity_provider_url,
                json=BILLING_SERVICE_MANIFEST,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully registered billing service manifest: {response.json()}")
            else:
                logger.error(f"Failed to register manifest: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"Error registering service manifest: {e}")
