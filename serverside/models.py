from typing import Optional
from uuid import uuid4

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import connection, connections
from django.db.models import QuerySet

from serverside.backends import get_backend


class UserQuerySet(QuerySet):
    DEFAULT_DATABASE = "default"

    def delete(self):
        backend = get_backend(self._db or self.DEFAULT_DATABASE)
        for user in self:
            backend.delete_user(user.username)
            user.delete()

    def bulk_create(
        self, objs, batch_size: Optional[int] = None, ignore_conflicts: bool = False
    ):
        raise NotImplementedError("Database users cannot be created in bulk.")

    def bulk_update(self, objs, fields, batch_size: Optional[int] = None) -> int:
        raise NotImplementedError("Database users cannot be updated in bulk.")


class UserManager(DjangoUserManager):
    def get_queryset(self):
        return UserQuerySet(self.model, using=self._db)


class User(AbstractUser):
    DEFAULT_DATABASE = "default"

    objects = UserManager()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._backend = get_backend(self._state.db or self.DEFAULT_DATABASE)
        self._dbusername = f"tmp_{uuid4()}" if not self.username else self.username

    def __user_table_exists(self):
        db = self._state.db
        cursor = connections[db].cursor() if db else connection.cursor()
        return self._meta.db_table in connection.introspection.get_table_list(cursor)

    def __set_backend(self, dbname: Optional[str] = None):
        backend = get_backend(dbname or self.DEFAULT_DATABASE)

        if self._backend is None or not self._backend:
            self._backend = backend
            return

        if type(self._backend) is type(backend):
            return

        if self._backend.user_exists(self._username):
            raise Exception("Cannot switch backend after creating a temporary user.")

        self._backend = backend

    def __del__(self):
        # Remove users from the database that may have been only temporary.
        # This is not relevant, if the User model does not yet have a table (i.e. if
        # the code was run in the context of makemigrations).
        if self.__user_table_exists() and not User.objects.filter(pk=self.pk).exists():
            self._backend.delete_user(self._dbusername)

    def set_password(self, raw_password):
        super().set_password(raw_password)

        if not self._backend.user_exists(self._dbusername):
            self._backend.create_user(self._dbusername, raw_password)
        else:
            self._backend.change_password(self._dbusername, raw_password)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Rename existing user, if necessary.
        if self._dbusername != self.username and self._backend.user_exists(
            self._dbusername
        ):
            self._backend.rename_user(self._dbusername, self.username)
        self._dbusername = self.username

        self.__set_backend(kwargs.get("using", None) or self._state.db)
        if not self._backend.user_exists(self._dbusername):
            self._backend.create_user(self._dbusername)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self._backend.delete_user(self._dbusername)
