from serverside import utils


def create_permissions(*args, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType

    # Workaround for a decade-old bug in django:
    # See here: https://code.djangoproject.com/ticket/10827#no1 and
    # here: https://github.com/pytest-dev/pytest-django/issues/18
    ContentType.objects.clear_cache()

    models = utils.get_all_models(True, False)
    for m in models:
        codename = utils.get_permission_codename("select", m)
        name = f"Can SELECT from {m._meta.db_table} table"
        content_type = ContentType.objects.get_for_model(m)

        Permission.objects.update_or_create(
            codename=codename, defaults={"name": name, "content_type": content_type}
        )
