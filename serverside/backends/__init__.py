from typing import Optional

from django.conf import settings
from django.db import connections

from serverside.backends.base import BackendBase


def get_backend(using: Optional[str] = None) -> Optional[BackendBase]:
    if not using:
        return None

    name = settings.DATABASES[using]["ENGINE"].split(".")[-1]

    for cls in BackendBase.__subclasses__():
        if cls.__name__.lower() == name.lower():
            return cls(connections[using].cursor())  # type: ignore
    return None
