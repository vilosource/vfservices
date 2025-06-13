import logging
import os

from django.apps import AppConfig


class IdentityAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "identity_app"

    def ready(self) -> None:
        """Ensure a default admin user exists when the app starts."""
        print("DEBUG: IdentityAppConfig.ready() called")
        if os.environ.get("RUN_MAIN") != "true":
            print("DEBUG: Skipping admin user creation - not main process")
            return
        print("DEBUG: About to call _ensure_default_admin()")
        self._ensure_default_admin()

    def _ensure_default_admin(self) -> None:
        """Create a default admin user if none exists."""
        from django.contrib.auth import get_user_model
        from django.db.utils import OperationalError, ProgrammingError

        print("DEBUG: _ensure_default_admin() called - Ensuring default admin user exists...")

        logger = logging.getLogger(__name__)
        User = get_user_model()

        try:
            User.objects.get(username="admin")
            print("DEBUG: Admin user already exists")
        except User.DoesNotExist:
            try:
                User.objects.create_superuser(
                    "admin",
                    "admin@example.com",
                    "admin",
                )
                logger.info("Created default admin user")
                print("DEBUG: Successfully created default admin user")
            except (OperationalError, ProgrammingError) as exc:
                logger.warning("Could not create admin user: %s", exc)
                print(f"DEBUG: Failed to create admin user: {exc}")
        except (OperationalError, ProgrammingError) as exc:
            logger.warning("Admin user check failed: %s", exc)
            print(f"DEBUG: Admin user check failed: {exc}")
