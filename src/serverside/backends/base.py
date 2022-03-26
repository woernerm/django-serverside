"""
This module contains a common interface definition for all backends.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Union


class BackendBase(ABC):
    """
    Base class for a database backend. It defines a common interface for all backends.
    """

    @abstractmethod
    def __init__(self, cursor) -> None:
        """
        Initializes the backend.

        Args:
            cursor: Database cursor.
        """
        pass

    @abstractmethod
    def create_user(
        self,
        username: str,
        password: Optional[str] = None,
        expires: Optional[datetime] = None,
        conn_limit: Optional[int] = None,
    ) -> None:
        """
        Create the user in the database, if it does not exist already.

        Args:
            username: The name of the user to create.
            password: The password the user shall have.
            expires: The date and time when the user's password shall expire. If the
                password shall never expire, use None (default).
            conn_limit: The number of concurrent connections of the user. If there shall
                be no limit, use None (default).

        Raises:
            Exception: If the user already exists.
        """
        pass

    @abstractmethod
    def delete_user(self, username: str) -> None:
        """
        Delete the user in the database.

        Args:
            username: The name of the user to delete.
        """
        pass

    @abstractmethod
    def user_exists(self, username: str) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.

        Args:
            username: The username that shall be checked for existence.
        """
        pass

    @abstractmethod
    def rename_user(self, oldname: str, newname: str) -> None:
        """
        Renames a database user.

        Args:
            oldname: The username the database currently uses.
            newname: The new username of the user.
        """
        pass

    @abstractmethod
    def change_password(self, username: str, password: str) -> None:
        """
        Change the password of the user.

        Args:
            username: The username of the user whose password shall be changed.
            password: The new password of the user.

        Raises:
            Exception: If the operation fails.
        """
        pass

    @abstractmethod
    def grant(
        self, username: str, privilege: str, type_name: str, objects: Union[List, str]
    ) -> None:
        """
        Grants privileges on the given objects.

        Args:
            username: The name of the user who shall be granted a privilege.
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        pass

    @abstractmethod
    def revoke(
        self, username: str, privilege: str, type_name: str, objects: Union[List, str]
    ) -> None:
        """
        Revokes privileges on the given objects.

        Args:
            username: The name of the user who shall have a privilege revoked.
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        pass
