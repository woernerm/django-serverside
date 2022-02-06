from datetime import datetime, timezone

from django.db import connection
from django.test import TestCase
from django.conf import settings
from psycopg2 import sql

from serverside.backends import get_backend


class TestBackend(TestCase):
    def test_get_backend_shall_return_a_backend_object(self):
        self.assertIsNone(get_backend(""))
        self.assertIsNone(get_backend(None))
        self.assertIsNotNone(get_backend("default"))

