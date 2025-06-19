import logging
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class IdentityAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity_app"

    def ready(self) -> None:
        """App is ready - perform any necessary initialization."""
        # Import and connect RBAC-ABAC signals
        from . import signals
        signals.connect_signals()
        
        # Register our own service manifest
        self.register_self()
    
    def register_self(self):
        """Register the identity provider's own service manifest."""
        try:
            # Import here to avoid app registry issues
            from .services import ManifestService
            from .manifest import SERVICE_MANIFEST
            
            logger.info("Registering Identity Provider service manifest...")
            
            # Register our own manifest
            result = ManifestService.register_manifest(
                manifest_data=SERVICE_MANIFEST,
                ip_address=None  # No IP address for self-registration
            )
            
            logger.info(f"Identity Provider service registered: {result}")
            
        except Exception as e:
            logger.error(f"Failed to register Identity Provider service: {e}")
