from django.apps import AppConfig


class IdentityAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity_app"

    def ready(self) -> None:
        """App is ready - perform any necessary initialization."""
        # Import signal handlers or other app initialization code here
        pass
