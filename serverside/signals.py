from itertools import chain

from django.apps import apps


def create_permissions(sender, app_config, verbosity, interactive, *args, **kwargs):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    
    applist = apps.get_app_configs()
    models = [a.get_models(True, False) for a in applist]
    models = chain.from_iterable(models)
    for m in models:
        codename = f"can_select_{m._meta.model_name}"
        name = f"Can SELECT from {m._meta.verbose_name}"
        content_type = ContentType.objects.get_for_model(m)

        Permission.objects.update_or_create(
                codename=codename,
                defaults={"name": name, "content_type":content_type}
        )
    
