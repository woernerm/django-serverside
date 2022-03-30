from django.test import TestCase
from django.contrib.auth.models import Permission
from django.db import connection
from django.contrib.auth.models import AbstractUser
from psycopg2 import sql

from serverside import utils
from serverside.models import User
from serverside.signals import create_permissions_and_grant_privileges


class TestPermissions(TestCase):
    def test_create_permissions_shall_create_permissions_for_all_models(self):
        models = utils.get_all_models(True, False)
        self.assertGreater(len(models), 1)

        for m in models:
            codename = utils.get_permission_codename("select", m)
            permissions = Permission.objects.filter(codename=codename)
            self.assertIsNotNone(permissions)
            self.assertEqual(permissions.count(), 1)

    def test_assigning_a_permission_shall_grant_a_privilege(self):
        cursor = connection.cursor()
        models = utils.get_all_models(True, False)
        name = "John Doe"
        password = "12345"
        privilege = "select"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            permission = Permission.objects.filter(codename=codename).first()
            user.user_permissions.add(permission)
        user.save()

        # Requesting new instance of the user, because permissions are cached as 
        # outlined here: 
        # https://docs.djangoproject.com/en/4.0/topics/auth/default/#topic-authorization
        user = User.objects.get(pk=user.pk)

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        data = cursor.fetchall()
        granted_tables = [t[0] for t in data]

        # Check, whether all assigned permissions were indeed given. Both as django
        # permission and as database permission.
        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            table = m._meta.db_table
            perm_name = f"{m._meta.app_label}.{codename}"
            has_perm = user.has_perm(perm_name)
            self.assertTrue(has_perm)
            self.assertTrue(table in granted_tables)

    def test_removing_a_permission_shall_revoke_a_privilege(self):
        cursor = connection.cursor()
        models = utils.get_all_models(True, False)
        name = "John Doe"
        password = "12345"
        privilege = "select"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            permission = Permission.objects.filter(codename=codename).first()
            user.user_permissions.add(permission)
        user.save()

        # Requesting new instance of the user, because permissions are cached as 
        # outlined here: 
        # https://docs.djangoproject.com/en/4.0/topics/auth/default/#topic-authorization
        user = User.objects.get(pk=user.pk)

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        data = cursor.fetchall()
        granted_tables = [t[0] for t in data]

        # Check, whether all assigned permissions were indeed given. Both as django
        # permission and as database permission.
        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            table = m._meta.db_table
            perm_name = f"{m._meta.app_label}.{codename}"
            has_perm = user.has_perm(perm_name)
            self.assertTrue(has_perm)
            self.assertTrue(table in granted_tables)

        # ****************************************
        # ********** Revoke permissions **********
        # ****************************************
        user.user_permissions.set(list())
        user.save()

        # Requesting new instance of the user, because permissions are cached as 
        # outlined here: 
        # https://docs.djangoproject.com/en/4.0/topics/auth/default/#topic-authorization
        user = User.objects.get(pk=user.pk)

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        data = cursor.fetchall()
        granted_tables = [t[0] for t in data]

        # Check, whether all assigned permissions were indeed revoked. Both as django
        # permission and as database permission.
        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            table = m._meta.db_table
            perm_name = f"{m._meta.app_label}.{codename}"
            has_perm = user.has_perm(perm_name)
            self.assertFalse(has_perm)
            self.assertFalse(table in granted_tables)

    def test_update_db_permissions_shall_return_without_action_if_there_is_no_db_user(self):
        cursor = connection.cursor()
        models = utils.get_all_models(True, False)
        name = "John Doe"
        password = "12345"
        privilege = "select"

        user = User.objects.create(username=name, password=password, has_dbuser=False)
        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            permission = Permission.objects.filter(codename=codename).first()
            user.user_permissions.add(permission)
        user.save()
        user.update_db_permissions()

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        self.assertIsNone(cursor.fetchone())

    def test_update_db_permissions_shall_grant_privileges_if_there_is_a_db_user(self):
        cursor = connection.cursor()
        models = utils.get_all_models(True, False)
        name = "John Doe"
        password = "12345"
        privilege = "select"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            permission = Permission.objects.filter(codename=codename).first()
            user.user_permissions.add(permission)
        super(AbstractUser, user).save()

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        self.assertIsNone(cursor.fetchone())

        user.update_db_permissions()

        cursor.execute(query, (privilege.upper(), name))
        data = cursor.fetchall()
        granted_tables = [t[0] for t in data]

        for m in models:
            table = m._meta.db_table
            self.assertIn(table, granted_tables)

    def test_create_permissions_and_grant_privileges_shall_grant_privileges_if_there_is_a_db_user(self):
        cursor = connection.cursor()
        models = utils.get_all_models(True, False)
        name = "John Doe"
        password = "12345"
        privilege = "select"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

        for m in models:
            codename = utils.get_permission_codename(privilege.lower(), m)
            permission = Permission.objects.filter(codename=codename).first()
            user.user_permissions.add(permission)
        super(AbstractUser, user).save()

        query = sql.SQL("SELECT DISTINCT table_name from "
            "information_schema.table_privileges WHERE privilege_type=%s AND "
            "grantee = %s")
        cursor.execute(query, (privilege.upper(), name))
        self.assertIsNone(cursor.fetchone())

        create_permissions_and_grant_privileges()

        cursor.execute(query, (privilege.upper(), name))
        data = cursor.fetchall()
        granted_tables = [t[0] for t in data]

        for m in models:
            table = m._meta.db_table
            self.assertIn(table, granted_tables)




