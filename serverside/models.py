from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import connection, connections
from django.db.models import QuerySet

from serverside.backends import DBUser, get_backend


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
        self._dbuser = DBUser(self._state.db or self.DEFAULT_DATABASE, self.username)

    def has_table(self):
        db = self._state.db
        cursor = connections[db].cursor() if db else connection.cursor()
        return self._meta.db_table in connection.introspection.get_table_list(cursor)

    def __del__(self):
        # Remove users from the database that may have been only temporary.
        # This is not relevant, if the User model does not yet have a table (i.e. if
        # the code was run in the context of makemigrations).
        if self.has_table() and not User.objects.filter(pk=self.pk).exists():
            self._dbuser.delete()

    def set_password(self, raw_password):
        super().set_password(raw_password)

        self._dbuser.change_password(raw_password)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        self._dbuser.username = self.username
        self._dbuser.save(kwargs.get("using", None) or self._state.db)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        self._dbuser.delete()
