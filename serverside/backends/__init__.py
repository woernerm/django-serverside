from importlib import import_module
from inspect import getmembers, isclass
from typing import List, Optional, Union
from uuid import uuid4

from django.conf import settings
from django.db import connections


def get_backend(using: Optional[str] = None):
    if not using:
        return None

    name = settings.DATABASES[using]["ENGINE"].split(".")[-1]
    module = import_module(f"serverside.backends.{name}")

    for _, obj in getmembers(module, isclass):
        if obj.__name__.lower() == name.lower():
            return obj(connections[using].cursor())
    return None


class DBUser:
    """
    Allows to manage a user in a relational database.
    """

    DEFAULT_DATABASE = "default"

    def __init__(self, using: str, username: Optional[str] = None) -> None:
        """
        Initializes the user. If no name is given, a random name will be chosen.

        The random name has the format tmp_user_ followed by a random identifier.

        Args:
            cursor: The database cursor according to PEP 249.
            name: The name of the user.
        """
        self._backend = get_backend(using)
        self._username = f"tmp_user_{uuid4()}" if not username else username

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, name):
        # Rename existing user, if necessary.
        if self.username != name and self._backend.user_exists(self._username):
            self._backend.rename_user(self._username, name)
        self._username = name

    def using(self, dbname: Optional[str] = None):
        backend = get_backend(dbname or self.DEFAULT_DATABASE)

        if self._backend is None or not self._backend:
            self._backend = backend
            return

        if type(self._backend) is type(backend):
            return

        if self._backend.user_exists(self._username):
            raise Exception("Cannot switch backend after creating a temporary user.")

        self._backend = backend

    def save(self, using: Optional[str] = None) -> None:
        """
        Create the user in the database, if it does not exist already.

        Args:
            password: The password the user shall have.

        Raises:
            Exception: If the user already exists.
        """
        self.using(using)

        if not self._backend.user_exists(self.username):
            self._backend.create_user(self._username)

    def delete(self) -> None:
        """
        Delete the user in the database.
        """
        self._backend.delete_user(self._username)

    def exists(self) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.
        """
        return bool(self._backend.user_exists(self._username))

    def change_password(self, password: str) -> None:
        """
        Change the password of the user.

        Args:
            password: The new password of the user.

        Raises:
            Exception: If the operation fails.
        """
        if not self._backend.user_exists(self.username):
            self._backend.create_user(self.username, password)
        else:
            self._backend.change_password(self.username, password)

    def rename(self, username: str) -> None:
        """
        Change the name of the user

        Args:
            username: The new name of the user.

        Raises:
            Exception: If the operation fails.
        """
        self._backend.rename_user(self._username, username)
        self._username = username

    def grant(self, privilege: str, type_name: str, objects: Union[List, str]) -> None:
        """
        Grants select privileges on the given tables.

        Args:
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        self._backend.grant(self._username, privilege, type_name, objects)

    def revoke(self, privilege: str, type_name: str, objects: Union[List, str]) -> None:
        """
        Revokes privileges on the given objects.

        Args:
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        self._backend.revoke(self._username, privilege, type_name, objects)
