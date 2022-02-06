# Try to use django's TestCase. If django is not installed, default to unittest.
from datetime import datetime, timedelta, timezone

from django.db import connection
from django.test import TestCase
from psycopg2 import sql

from serverside.backends.postgresql import PostgreSQL


class TestCreate(TestCase):
    def test_create_shall_create_a_PostgreSQL(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        backend.create_user(name, password)

        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

    def test_create_with_no_password_shall_create_a_user_that_cannot_login(self):
        cursor = connection.cursor()
        name = "John Doe"
        backend = PostgreSQL(cursor)
        backend.create_user(name)
        command = cursor.query.decode()

        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Verify that the correct password parameter is contained in the query.
        self.assertTrue("PASSWORD NULL" in command)

    def test_create_shall_raise_an_exception_for_an_existing_PostgreSQL_user(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        backend.create_user(name, password)

        with self.assertRaises(Exception):
            backend.create_user(name, password)

    def test_create_shall_create_a_user_with_limited_validity(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        expires = datetime.now(timezone.utc) + timedelta(days=1)
        backend.create_user(name, password, expires)

        query = sql.SQL(
            "SELECT rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname = %s"
        )
        cursor.execute(query, (name,))
        result_limit, result_expire = cursor.fetchone()
        self.assertEqual(-1, result_limit)
        self.assertEqual(expires, result_expire)

    def test_create_shall_create_a_user_with_limited_connections(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        conn_limit = 42
        backend = PostgreSQL(cursor)
        backend.create_user(name, password, None, conn_limit)

        query = sql.SQL(
            "SELECT rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname = %s"
        )
        cursor.execute(query, (name,))
        result_limit, result_expire = cursor.fetchone()
        self.assertEqual(conn_limit, result_limit)
        self.assertEqual(None, result_expire)

    def test_create_shall_create_a_user_with_connection_and_validity_limit(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        conn_limit = 42
        expires = datetime.now(timezone.utc) + timedelta(days=1)
        backend = PostgreSQL(cursor)
        backend.create_user(name, password, expires, conn_limit)

        query = sql.SQL(
            "SELECT rolconnlimit, rolvaliduntil FROM pg_roles WHERE rolname = %s"
        )
        cursor.execute(query, (name,))
        result_limit, result_expire = cursor.fetchone()
        self.assertEqual(conn_limit, result_limit)
        self.assertEqual(expires, result_expire)


class TestBulkCreate(TestCase):
    def test_bulk_create_user_shall_create_a_PostgreSQL_user(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        backend.bulk_create_user([{"username": name, "password": password}])

        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

    def test_bulk_create_user_shall_create_multiple_PostgreSQL_users(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        password1 = "12345"
        name2 = "Max Mustermann"
        password2 = "54321"
        backend = PostgreSQL(cursor)
        backend.bulk_create_user([{"username": name1, "password": password1}, {"username": name2, "password": password2}])

        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name1,))
        self.assertIsNotNone(cursor.fetchone())

        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name2,))
        self.assertIsNotNone(cursor.fetchone())

    def test_bulk_create_user_shall_raise_an_exception_for_an_existing_PostgreSQL_users(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        backend.create_user(name, password)

        with self.assertRaises(Exception):
            backend.bulk_create_user({"username": name, "password":password})

    def test_bulk_create_user_shall_raise_exception_for_invalid_parameters(self):
        cursor = connection.cursor()
        nm = "John Doe"
        pw = "12345"
        backend = PostgreSQL(cursor)

        with self.assertRaises(Exception):
            backend.bulk_create_user({"username": nm, "password":pw, "conn_limit": -1})

        with self.assertRaises(Exception):
            backend.bulk_create_user({"username": nm, "password":pw, "conn_limit": -1})

        with self.assertRaises(Exception):
            backend.bulk_create_user({"username": nm, "password":pw, "expires": 42})

        with self.assertRaises(Exception):
            backend.bulk_create_user({"username": nm, "password":pw, "expires": datetime.now()})


class TestExists(TestCase):
    def test_exists_shall_return_false_if_no_user_exists(self):
        cursor = connection.cursor()
        name = "John Doe"
        backend = PostgreSQL(cursor)
        self.assertFalse(backend.user_exists(name))

    def test_exists_shall_return_true_if_user_exists(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)
        backend.create_user(name, password)

        self.assertTrue(backend.user_exists(name))


class TestChangePassword(TestCase):
    def test_change_password_shall_change_the_user_password(self):
        cursor = connection.cursor()
        name = "John Doe"
        old_password = "12345"
        new_password = "54321"
        backend = PostgreSQL(cursor)
        backend.create_user(name, old_password)
        backend.change_password(name, new_password)

        # No other way known for checking that the function works than to compare
        # the query with a command that is known to work.
        command = cursor.query.decode()
        expected_command = f"ALTER ROLE \"{name}\" PASSWORD '{new_password}'"
        self.assertEqual(command, expected_command)


class TestGrant(TestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._single_table_name = "test_table_1"
        self._multiple_table_name = ["test_table_2", "test_table_3"]

    def setUp(self):
        cursor = connection.cursor()
        query = sql.SQL("CREATE TABLE {name}(test_field integer);").format(
            name=sql.Identifier(self._single_table_name)
        )

        for name in self._multiple_table_name:
            query += sql.SQL("CREATE TABLE {name}(test_field integer);").format(
                name=sql.Identifier(name)
            )

        cursor.execute(query)

    def get_privileges(self, username):
        cursor = connection.cursor()
        query = sql.SQL(
            "SELECT table_name, privilege_type "
            "FROM   information_schema.table_privileges WHERE  grantee = {name}"
        ).format(name=sql.Literal(username))
        cursor.execute(query)
        return cursor.fetchall()

    def test_grant_shall_grant_privilege(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name, password)
        backend.grant(name, "select", "table", self._single_table_name)

        result = self.get_privileges(name)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], self._single_table_name)

        # Test the grant to multiple tables.
        backend.grant(name, "select", "table", self._multiple_table_name)

        result = self.get_privileges(name)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0][0], self._single_table_name)
        for i, tbl in enumerate(self._multiple_table_name):
            self.assertEqual(result[i + 1][0], tbl)

    def test_grant_shall_raise_exception_for_invalid_parameters(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name, password)

        with self.assertRaises(Exception):
            backend.grant(name, "selected", "table", self._single_table_name)

        with self.assertRaises(Exception):
            backend.grant(name, "selected", "tablesd", self._single_table_name)

        with self.assertRaises(Exception):
            backend.grant(name, "selected", "tables", "non_existent")


class TestRevoke(TestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._single_table_name = "test_table_1"
        self._multiple_table_name = ["test_table_2", "test_table_3"]

    def setUp(self):
        cursor = connection.cursor()
        query = sql.SQL("CREATE TABLE {name}(test_field integer);").format(
            name=sql.Identifier(self._single_table_name)
        )

        for name in self._multiple_table_name:
            query += sql.SQL("CREATE TABLE {name}(test_field integer);").format(
                name=sql.Identifier(name)
            )

        cursor.execute(query)

    def get_privileges(self, username):
        cursor = connection.cursor()
        query = sql.SQL(
            "SELECT table_name, privilege_type "
            "FROM   information_schema.table_privileges WHERE  grantee = {name}"
        ).format(name=sql.Literal(username))
        cursor.execute(query)
        return cursor.fetchall()

    def test_revoke_shall_revoke_privilege(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name, password)
        backend.grant(name, "select", "table", self._single_table_name)
        backend.grant(name, "select", "table", self._multiple_table_name)

        result = self.get_privileges(name)
        self.assertEqual(len(result), 3)
        tables = [result[i][0] for i in range(3)]
        self.assertTrue(self._single_table_name in tables)
        for tbl in self._multiple_table_name:
            self.assertTrue(tbl in tables)

        # Test the revoke for single table.
        backend.revoke(name, "select", "table", self._single_table_name)

        result = self.get_privileges(name)
        self.assertEqual(len(result), 2)
        tables = [result[i][0] for i in range(2)]
        for tbl in self._multiple_table_name:
            self.assertTrue(tbl in tables)

        # Test the revoke for multiple tables.
        backend.revoke(name, "select", "table", self._multiple_table_name)
        result = self.get_privileges(name)
        self.assertEqual(len(result), 0)


class TestDelete(TestCase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._multiple_table_name = ["test_table_2", "test_table_3"]

    def setUp(self):
        cursor = connection.cursor()
        query = []

        for name in self._multiple_table_name:
            query.append(
                sql.SQL("CREATE TABLE {name}(test_field integer);").format(
                    name=sql.Identifier(name)
                )
            )

        cursor.execute(sql.SQL("").join(query))

    def test_delete_shall_delete_PostgreSQL(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        name2 = "John Smith"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name1, password)
        backend.create_user(name2, password)

        self.assertTrue(backend.user_exists(name1))
        self.assertTrue(backend.user_exists(name2))

        backend.delete_user(name1)
        self.assertFalse(backend.user_exists(name1))
        self.assertTrue(backend.user_exists(name2))

        backend.delete_user(name2)
        self.assertFalse(backend.user_exists(name1))
        self.assertFalse(backend.user_exists(name2))

    def test_delete_shall_revoke_privileges_before_user_deletion(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name, password)
        backend.grant(name, "select", "table", self._multiple_table_name)
        self.assertTrue(backend.user_exists(name))

        backend.delete_user(name)
        self.assertFalse(backend.user_exists(name))


class TestRename(TestCase):
    def test_rename_shall_change_the_name_of_the_PostgreSQL(self):
        cursor = connection.cursor()
        name = "John Doe"
        newname = "Max Mustermann"
        password = "12345"
        backend = PostgreSQL(cursor)

        backend.create_user(name, password)

        self.assertFalse(backend.user_exists(newname))
        self.assertTrue(backend.user_exists(name))
        backend.rename_user(name, newname)
        self.assertFalse(backend.user_exists(name))
        self.assertTrue(backend.user_exists(newname))
