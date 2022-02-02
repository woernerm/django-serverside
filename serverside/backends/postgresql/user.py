from datetime import datetime
from typing import List, Optional, Union

from psycopg2 import sql


class UserMixin:
    """
    Allows to manage a user in a relational database.
    """

    __PRIVILEGES = {
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "TRUNCATE",
        "REFERENCES",
        "TRIGGER",
        "CREATE",
        "CONNECT",
        "TEMPORARY",
        "EXECUTE",
        "USAGE",
    }

    __GRANT_TYPES = {
        "TABLE",
        "SEQUENCE",
        "DATABASE",
        "FOREIGN DATA WRAPPER",
        "FOREIGN SERVER",
        "FUNCTION",
        "LANGUAGE",
        "LARGE OBJECT",
        "SCHEMA",
        "TABLESPACE",
    }

    __PRIVILEGE_OPERATIONS = {"GRANT", "REVOKE"}

    __POSTGRESQL_SCHEMAS = {
        "information_schema",
        "pg_roles",
        "pg_statistic",
        "pg_catalog",
    }

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
            password: The password the user shall have. If None is given, login will
                always fail for PostgreSQL 8.2 or later.
            expires: The date and time when the user's password shall expire. If the
                password shall never expire, use None (default).
            conn_limit: The number of concurrent connections of the user. If there shall
                be no limit, use None (default).

        Raises:
            Exception: If the user already exists.
        """
        if conn_limit is not None and conn_limit < 0:
            raise ValueError("Parameter conn_limit must be positive or None.")

        if expires is not None and type(expires) is not datetime:
            raise TypeError("Parameter expires is not a datetime object.")

        if expires is not None and (
            expires.tzinfo is None or expires.tzinfo.utcoffset(expires) is None
        ):
            raise TypeError("Parameter expires is a naive. Provide a timezone.")

        limit = -1 if conn_limit is None else conn_limit
        valid = sql.SQL("")

        if expires is not None:
            valid = sql.SQL("VALID UNTIL ") + sql.Literal(expires.isoformat())

        query = sql.SQL(
            "CREATE ROLE {name} WITH LOGIN INHERIT CONNECTION LIMIT %s "
            "PASSWORD %s {valid}"
        ).format(name=sql.Identifier(username), valid=valid)

        self._cursor.execute(
            query,
            (
                limit,
                password,
            ),
        )

    def delete_user(self, username: str) -> None:
        """
        Delete the user in the database.
        """

        self._cursor.execute("SELECT CURRENT_DATABASE()")
        db_name = self._cursor.fetchone()[0]

        self._cursor.execute("SELECT schema_name FROM information_schema.schemata;")
        schemas = self._cursor.fetchall()

        revokes = list()
        revokes.append(
            sql.SQL("REVOKE ALL ON DATABASE {db} FROM {n}").format(
                db=sql.Identifier(db_name), n=sql.Identifier(username)
            )
        )

        for schema in schemas:
            schema = str(schema[0])

            if schema in self.__POSTGRESQL_SCHEMAS:
                continue  # Ignore schemas from postgresql.

            revokes.append(
                sql.SQL(
                    "REVOKE ALL ON SCHEMA {s} FROM {n};"
                    "REVOKE ALL ON ALL TABLES IN SCHEMA {s} FROM {n};"
                    "REVOKE ALL ON ALL SEQUENCES IN SCHEMA {s} FROM {n};"
                    "REVOKE ALL ON ALL FUNCTIONS IN SCHEMA {s} FROM {n}"
                ).format(s=sql.Identifier(schema), n=sql.Identifier(username))
            )

        revokes = sql.SQL(";").join(revokes)

        # Roles cannot be simply droped. All privileges must first be revoked.
        # Otherwise, an error will be raised.
        query = sql.SQL(
            "DO $$BEGIN "
            "IF EXISTS (SELECT FROM pg_roles WHERE rolname = {name_lit} AND "
            "rolcanlogin='true') THEN EXECUTE '"
            "{revokes};"
            "'; END IF;"
            "END$$;"
            "DROP USER IF EXISTS {name_ident};"
        ).format(
            name_lit=sql.Literal(username),
            name_ident=sql.Identifier(username),
            db=sql.Identifier(db_name),
            revokes=revokes,
        )
        self._cursor.execute(query)

    def user_exists(self, username: str) -> bool:
        """
        Returns True, if the user already exists. False, otherwise.
        """
        query = sql.SQL("SELECT oid FROM pg_roles WHERE rolname = %s")

        self._cursor.execute(query, (username,))
        return self._cursor.fetchone() is not None

    def rename_user(self, oldname: str, newname: str) -> None:
        query = sql.SQL("ALTER ROLE {oldname} RENAME TO {newname}").format(
            oldname=sql.Identifier(oldname), newname=sql.Identifier(newname)
        )

        self._cursor.execute(query)

    def change_password(self, username: str, password: str) -> None:
        """
        Change the password of the user.

        Args:
            password: The new password of the user.

        Raises:
            Exception: If the operation fails.
        """
        query = sql.SQL("ALTER ROLE {name} PASSWORD %s").format(
            name=sql.Identifier(username)
        )
        self._cursor.execute(query, (password,))

    def _alter_privilege(
        self,
        username: str,
        operation: str,
        privilege: str,
        type_name: str,
        objects: Union[List, str],
    ):
        """
        Grants or revokes privileges on the given objects.

        Args:
            operation: Either "GRANT" or "REVOKE".
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        if privilege.upper() not in self.__PRIVILEGES:
            raise ValueError("Given privilege is unknown.")

        if type_name.upper() not in self.__GRANT_TYPES:
            raise ValueError("Given grant type is unknown.")

        if operation.upper() not in self.__PRIVILEGE_OPERATIONS:
            raise ValueError("Unknown operation.")

        object_names = [objects] if type(objects) is str else objects
        direction = sql.SQL("TO") if operation.upper() == "GRANT" else sql.SQL("FROM")

        # Compile the grants.
        cmds = []
        for objname in object_names:
            cmds.append(
                sql.SQL("{op} {priv} ON {tname} {oname} {direction} {user}").format(
                    op=sql.SQL(operation.upper()),
                    tname=sql.SQL(type_name.upper()),
                    oname=sql.Identifier(objname),
                    user=sql.Identifier(username),
                    priv=sql.SQL(privilege.upper()),
                    direction=direction,
                )
            )

        # Execute the compiled query.
        self._cursor.execute(sql.SQL(";").join(cmds))

    def grant(
        self, username: str, privilege: str, type_name: str, objects: Union[List, str]
    ) -> None:
        """
        Grants privileges on the given objects.

        Args:
            privilege: The name of the privilege to grant, e.g. "UPDATE" or "SELECT".
            type_name: The type of object the grant targets, e.g. "TABLE" or "DATABASE".
            objects: The object names the grant is for, e.g. the name of the tables to
                grant an "UPDATE" privilege to.

        Raises:
            Exception: If the operation fails.
        """
        self._alter_privilege(username, "GRANT", privilege, type_name, objects)

    def revoke(
        self, username: str, privilege: str, type_name: str, objects: Union[List, str]
    ) -> None:
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
        self._alter_privilege(username, "REVOKE", privilege, type_name, objects)
