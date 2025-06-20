from django.apps import AppConfig


class IdentityAdminConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'identity_admin'
    verbose_name = 'Identity Administration'
    
    def ready(self):
        """
        Initialize app when Django starts
        """
        pass