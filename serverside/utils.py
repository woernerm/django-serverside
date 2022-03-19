from itertools import chain
from typing import List

from django.apps import apps
from django.db.models import Model


def get_permission_codename(privilege: str, model: Model) -> str:
    return f"can_{privilege.lower()}_{model._meta.label}"


def get_all_models(include_auto_created: bool, include_swapped: bool) -> List[Model]:
    applist = apps.get_app_configs()
    models = [a.get_models(include_auto_created, include_swapped) for a in applist]
    return list(chain.from_iterable(models))
