"""
The file contains the app config required for Django.

You may read more about this here:
https://docs.djangoproject.com/en/4.0/ref/applications/
"""

from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .signals import create_permissions


class ServersideConfig(AppConfig):
    """
    App configuration class.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "serverside"
    verbose_name = "ServerSide"

    def ready(self):
        post_migrate.connect(create_permissions)
