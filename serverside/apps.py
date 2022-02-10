"""
The file contains the app config required for Django.

You may read more about this here:
https://docs.djangoproject.com/en/4.0/ref/applications/
"""

from django.apps import AppConfig


class ServersideConfig(AppConfig):
    """
    App configuration class.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "serverside"
    verbose_name = "ServerSide"
