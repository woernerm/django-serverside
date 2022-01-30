from pathlib import Path
from typing import Union

from jinja2 import Environment, FileSystemLoader
from psycopg2 import sql

from serverside.backends.base import BaseFunction


class FunctionMixin:
    def create_function(self, name: str, filename: Union[Path, str], **kwargs):
        """
        Creates the function in the database.

        If the function already exists, then it will be replaced.

        Raises:
            Exception: If the operation fails.
        """
        file = Path(filename) if type(filename) is str else filename
        env = Environment(loader=FileSystemLoader(str(file.parent)), autoescape=False)
        code = env.get_template(str(file.name)).render(**kwargs)

        query = sql.SQL("DROP FUNCTION IF EXISTS {name};\n").format(
            name=sql.Identifier(name)
        )
        query += sql.SQL(code)
        self._cursor.execute(sql.SQL(code))

    def delete_function(self, name: str):
        """
        Delete the function in the database.
        """
        query = sql.SQL("DROP FUNCTION IF EXISTS {name}").format(
            name=sql.Identifier(name)
        )
        self._cursor.execute(query)

    def function_exists(self, name: str) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.
        """
        query = sql.SQL("SELECT FROM pg_proc WHERE proname = {name}").format(
            name=sql.Literal(name)
        )
        self._cursor.execute(query)
        return self._cursor.fetchone() is not None
