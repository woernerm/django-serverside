# Try to use django's TestCase. If django is not installed, default to unittest.
from pathlib import Path

from django.db import connection
from django.test import TestCase
from psycopg2 import sql

from serverside.backends.postgresql import PostgreSQL


class TestCreate(TestCase):
    def test_create_shall_create_a_function(self):
        cursor = connection.cursor()
        name = "increment"
        filename = Path(__file__).parent / Path(f"./data/{name}.sql")
        backend = PostgreSQL(cursor)

        backend.create_function(name, filename)

        query = sql.SQL("SELECT FROM pg_proc WHERE proname = {name}").format(
            name=sql.Literal(name)
        )
        cursor.execute(query)
        self.assertIsNotNone(cursor.fetchone())


class TestExists(TestCase):
    def test_exists_shall_return_false_if_no_function_exists(self):
        cursor = connection.cursor()
        name = "increment"
        backend = PostgreSQL(cursor)

        self.assertFalse(backend.function_exists(name))

    def test_exists_shall_return_true_if_function_exists(self):
        cursor = connection.cursor()
        name = "increment"
        filename = Path(__file__).parent / Path(f"./data/{name}.sql")
        backend = PostgreSQL(cursor)

        backend.create_function(name, filename)
        self.assertTrue(backend.function_exists(name))


class TestDelete(TestCase):
    def test_delete_shall_delete_function(self):
        cursor = connection.cursor()
        name = "increment"
        filename = Path(__file__).parent / Path(f"./data/{name}.sql")
        backend = PostgreSQL(cursor)

        backend.create_function(name, filename)

        self.assertTrue(backend.function_exists(name))
        backend.delete_function(name)
        self.assertFalse(backend.function_exists(name))
