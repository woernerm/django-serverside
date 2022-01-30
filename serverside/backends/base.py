from pathlib import Path
from typing import List, Optional, Union
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader


class BaseUser:
    """
    Allows to manage a user in a relational database.
    """

    def __init__(self, cursor, name: Optional[str] = None) -> None:
        """
        Initializes the user. If no name is given, a random name will be chosen.

        The random name has the format tmp_user_ followed by a random identifier.

        Args:
            cursor: The database cursor according to PEP 249.
            name: The name of the user.
        """
        if name is not None and type(name) is not str:
            raise TypeError("Expected parameter name to be of type str.")

        print("Base initialized with ", name)
        self._cursor = cursor
        self._username = f"tmp_user_{uuid4()}" if not name else name

    @property
    def username(self):
        return self._username

    def create(self, password: Optional[str] = None) -> None:
        """
        Create the user in the database, if it does not exist already.

        Args:
            password: The password the user shall have.

        Raises:
            Exception: If the user already exists.
        """
        pass

    def delete(self) -> None:
        """
        Delete the user in the database.
        """
        pass

    def exists(self) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.
        """

    def change_password(self, password: str) -> None:
        """
        Change the password of the user.

        Args:
            password: The new password of the user.

        Raises:
            Exception: If the operation fails.
        """
        pass

    def rename(self, username: str) -> None:
        """
        Change the name of the user

        Args:
            username: The new name of the user.

        Raises:
            Exception: If the operation fails.
        """
        pass

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


class BaseFunction:
    """
    Represents a function in the SQL database (if supported).
    """

    def __init__(self, cursor, name: str, filename: Union[Path, str], **kwargs) -> None:
        """
        Initializes the function.

        Args:
            cursor: The database cursor according to PEP 249.
            name: The name of the function.
            filename: The name of the file containing the function template.
            args: Positional arguments for passing on to the template engine.
            kwargs: Keyworded arguments to pass on to the template engine.
        """
        self._cursor = cursor
        self._name = name

        file = Path(filename) if type(filename) is str else filename
        env = Environment(loader=FileSystemLoader(str(file.parent)), autoescape=True)
        self._code = env.get_template(str(file.name)).render(**kwargs)

    def create(self):
        """
        Creates the function in the database.

        Raises:
            Exception: If the operation fails.
        """
        pass

    def exists(self) -> bool:
        """
        Returns True, if the function already exists. False, otherwise.
        """

    def delete(self):
        """
        Deletes the function in the database.

        Raises:
            Exception: If the operation fails.
        """
        pass


class BaseView:
    """
    Represents a view in the database (if supported).
    """

    def __init__(self, cursor, name) -> None:
        """
        Initializes the view.

        Args:
            cursor: The database cursor according to PEP 249.
            name: The name of the view.
        """
        self._cursor = cursor
        self.name = name

    def create(self):
        """
        Create the view in the database, if it does not exist already.

        Raises:
            Exception: If the operation fails.
        """
        pass

    def exists(self) -> bool:
        """
        Returns True, if the view already exists. False, otherwise.
        """

    def delete(self):
        """
        Delete the view in the database.

        Raises:
            Exception: If the operation fails.
        """
        pass
