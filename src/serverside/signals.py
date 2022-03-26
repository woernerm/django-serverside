"""
This module defines functions that are called on a django signal such as post_migrate.
"""

from serverside import utils


def create_permissions(*args, **kwargs):
    """
    Creates database permissions to assign to a user.

    Creates django permissions that reflect what a corresponding database user is
    allowed to do when directly logged into the database. These permissions are
    translated into database privileges and granted to a user when a user is saved.

    Args:
        args: Postional arguments for compatibility. Not used.
        kwargs: Keyworded arguments for compatibility. Not used.
    """
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    # Workaround for a decade-old bug in django:
    # See here: https://code.djangoproject.com/ticket/10827#no1 and
    # here: https://github.com/pytest-dev/pytest-django/issues/18
    ContentType.objects.clear_cache()

    models = utils.get_all_models(True, False)
    for m in models:
        codename = utils.get_permission_codename("select", m)
        name = f"Can SELECT from {m._meta.db_table} table"  # nosec
        content_type = ContentType.objects.get_for_model(m)

        Permission.objects.update_or_create(
            codename=codename, defaults={"name": name, "content_type": content_type}
        )
