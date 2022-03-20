"""
This module defines utility functions used in various places of the package.
"""

from itertools import chain
from typing import List

from django.apps import apps
from django.db.models import Model


def get_permission_codename(privilege: str, model: Model) -> str:
    """
    Returns a standardized permission codename.

    Args:
        privilege: The name of the database privilege to create a codename for.
        model: The name of the model to create a permission codename for.

    Returns:
        The permission codename for the given database privilege and django model.
    """
    return f"can_{privilege.lower()}_{model._meta.db_table.lower()}"


def get_all_models(include_auto_created: bool, include_swapped: bool) -> List[Model]:
    """
    Returns all models of all installed django apps.

    In contrast to get_models() method of django's AppConfig class, this function
    returns the models of all installed apps.

    Args:
        include_auto_created: Whether to include auto-created models for many-to-many
            relations without an explicit intermediate table. Set to True to include
            them. False, otherwise.
        include_swapped: Whether to include models that have been swapped out. Set to
            True to include them. False, otherwise.

    Returns:
        List of all models of all installed django apps.
    """
    applist = apps.get_app_configs()
    models = [a.get_models(include_auto_created, include_swapped) for a in applist]
    return list(chain.from_iterable(models))
