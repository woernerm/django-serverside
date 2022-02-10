"""
Defines how server-side functions are created with PostgreSQL.
"""

from pathlib import Path
from typing import Union

from jinja2 import Environment, FileSystemLoader
from psycopg2 import sql


class FunctionMixin:
    """
    Mixin for managing and creating server-side functions.
    """

    def create_function(self, name: str, filename: Union[Path, str], **kwargs):
        """
        Creates the function in the database.

        If the function already exists, then it will be replaced.

        Args:
            name: The name of the function to be created.
            filename: The path to the file containing the functions' source code.
            kwargs: Keyword arguments which shall be passed to the template engine.
                These variables may then be used in the template to dynamically
                create / alter the functions code. This is useful to create multiple
                similar functions for different tables and types based on a common
                prototype.

        Raises:
            Exception: If the operation fails.
        """
        file = Path(filename) if type(filename) is str else filename
        env = Environment(loader=FileSystemLoader(str(file.parent)), autoescape=True)
        code = env.get_template(str(file.name)).render(**kwargs)

        query = sql.SQL("DROP FUNCTION IF EXISTS {name};\n").format(
            name=sql.Identifier(name)
        )
        query += sql.SQL(code)
        self._cursor.execute(sql.SQL(code))

    def delete_function(self, name: str):
        """
        Delete the function in the database.

        Args:
            name: The name of the function to delete.
        """
        query = sql.SQL("DROP FUNCTION IF EXISTS {name}").format(
            name=sql.Identifier(name)
        )
        self._cursor.execute(query)

    def function_exists(self, name: str) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.

        Args:
            name: The name of the functions which shall be checked for existence.

        Returns:
            True, if the function exists. False, otherwise.
        """
        query = sql.SQL("SELECT FROM pg_proc WHERE proname = {name}").format(
            name=sql.Literal(name)
        )
        self._cursor.execute(query)
        return self._cursor.fetchone() is not None
