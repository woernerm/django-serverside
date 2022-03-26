"""
Defines a backend class for the PostgreSQL database.
"""

from serverside.backends.base import BackendBase
from serverside.backends.postgresql.user import UserMixin


class PostgreSQL(UserMixin, BackendBase):
    """
    Backend class for PostgreSQL.
    """

    def __init__(self, cursor) -> None:
        """
        Initializes the backend.

        Args:
            cursor: Database cursor.
        """
        self._cursor = cursor
