"""
This module defines a convenience function for accessing the right backend class.
"""

from importlib import import_module
from inspect import getmembers, isclass
from typing import Optional

from django.conf import settings
from django.db import connections

from serverside.backends.base import BackendBase


def get_backend(using: Optional[str] = None) -> Optional[BackendBase]:
    """
    Selects and returns a backend class depending on the given database name.

    Multiple backends may be supported. Therefore, selecting the right one is best done
    using this convenience function. It uses Django's DATABASES setting and the given
    name (parameter using) to return the right backend class.

    Args:
        using: The settings.DATABASES entry that shall be used to select a backend.

    Returns:
        Specialized backend class. None, if no appropriate backend was found.
    """
    if not using:
        return None

    name = settings.DATABASES[using]["ENGINE"].split(".")[-1]
    module = import_module(f"serverside.backends.{name}")

    for _, cls in getmembers(module, isclass):
        if cls.__name__.lower() == name.lower():
            return cls(connections[using].cursor())  # type: ignore
    return None  # pragma: no cover
