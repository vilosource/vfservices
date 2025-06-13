import logging
import os

from django.apps import AppConfig


class IdentityAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity_app"

    def ready(self) -> None:
        """Ensure a default admin user exists when the app starts."""
        if os.environ.get("RUN_MAIN") != "true":
            # Avoid running twice when the autoreloader spawns a child process.
            return
        self._ensure_default_admin()

    def _ensure_default_admin(self) -> None:
        """Create a default admin user if none exists."""
        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError, ProgrammingError

        logger = logging.getLogger(__name__)
        User = get_user_model()

        try:
            User.objects.get(username="admin")
        except User.DoesNotExist:
            try:
                User.objects.create_superuser(
                    "admin",
                    "admin@example.com",
                    "admin",
                )
                logger.info("Created default admin user")
            except (OperationalError, ProgrammingError) as exc:
                logger.warning("Could not create admin user: %s", exc)
        except (OperationalError, ProgrammingError) as exc:
            logger.warning("Admin user check failed: %s", exc)
