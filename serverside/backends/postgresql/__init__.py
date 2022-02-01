from serverside.backends.base import BackendBase
from serverside.backends.postgresql.function import FunctionMixin
from serverside.backends.postgresql.user import UserMixin


class PostgreSQL(UserMixin, FunctionMixin, BackendBase):
    def __init__(self, cursor) -> None:
        self._cursor = cursor
