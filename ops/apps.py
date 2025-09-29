"""
App configuration for ops app.
"""
from django.apps import AppConfig


class OpsConfig(AppConfig):
    """Configuration class for ops app"""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ops'
    verbose_name = 'Operations Management'

    def ready(self):
        """Import signals when app is ready"""
        pass