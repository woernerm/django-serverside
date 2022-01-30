from serverside.backends.postgresql.function import FunctionMixin
from serverside.backends.postgresql.user import UserMixin


class PostgreSQL(UserMixin, FunctionMixin):
    def __init__(self, cursor) -> None:
        self._cursor = cursor
