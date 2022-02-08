from datetime import datetime, timezone

from django.db import connection
from django.test import TestCase
from psycopg2 import sql

from serverside.models import User


class TestSave(TestCase):
    def test_create_shall_create_a_new_user_in_database_and_django(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"

        User.objects.create(username=name, password=password, has_dbuser=True)

        # Is there a new user in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (name,))
        self.assertIsNotNone(cursor.fetchone())

        # Is there a new user in django (exactly one).
        self.assertEqual(User.objects.filter(username=name).count(), 1)

    def test_set_backend_shall_select_the_right_backend(self):
        name = "John Doe"
        password = "12345"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        user._backend = None
        user._set_backend(None)
        self.assertIsNotNone(user._backend)

    def test_set_backend_shall_not_switch_backends_if_temporary_user_has_been_created(self):
        from serverside.backends.postgresql import PostgreSQL
        name = "John Doe"
        password = "12345"

        class MockTrue:
            def __init__(self) -> None:
                self.username = None

            def user_exists(self, username):
                return True

        class MockFalse:
            def __init__(self) -> None:
                self.username = None

            def user_exists(self, username):
                return False

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        user._backend = MockTrue()
        with self.assertRaises(Exception):
            user._set_backend(None)  

        user._backend = MockFalse()   
        user._set_backend(None)   
        self.assertTrue(isinstance(user._backend, PostgreSQL)) 

    def test_changing_the_username_shall_rename_the_database_user(self):
        cursor = connection.cursor()
        name = "John Doe"
        newname = "Max Mustermann"
        password = "12345"

        user = User.objects.create(username=name, password=password, has_dbuser=True)
        user.username = newname
        user.save()

        # Is there a user with the new name in the database?
        query = sql.SQL("SELECT FROM pg_roles WHERE rolname = %s")
        cursor.execute(query, (newname,))
        self.assertIsNotNone(cursor.fetchone())

        # Has the user with the old name vanished?
        cursor.execute(query, (name,))
        self.assertIsNone(cursor.fetchone())

        # Is there a user with the new name in django (exactly one).
        self.assertEqual(User.objects.filter(username=newname).count(), 1)

        # Is there no user with the old name in django.
        self.assertFalse(User.objects.filter(username=name).exists())

    def test_db_user_shall_be_deleted_if_django_user_is_deleted(self):
        name = "John Doe"

        user = User.objects.create(username=name, has_dbuser=True)
        User.objects.filter(pk=user.pk).delete()
        user.__del__()


    def test_setting_the_password_with_no_db_user_shall_do_nothing(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"

        oldquery = cursor.query
        user = User.objects.create(username=name, has_dbuser=False)
        user.set_password(password)

        # Previous query has not changed.
        self.assertEqual(cursor.query, oldquery)
        

    def test_setting_the_password_shall_reate_a_temporary_user_in_database(self):
        cursor = connection.cursor()
        name = "John Doe"
        password = "12345"
        new_password = "54321"

        # Count the number of users.
        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_prior = len(cursor.fetchall())

        user = User(username=name, has_dbuser=True)
        user._state.db = connection.alias
        user.set_password(password)

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_first_pw_change = len(cursor.fetchall())

        # Exactly one user has been created in the database.
        self.assertEqual(num_users_prior + 1, num_users_first_pw_change)

        django_hash_prior = user.password
        user.set_password(new_password)
        django_hash_posterior = user.password

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_second_pw_change = len(cursor.fetchall())

        # No additional user has been created.
        self.assertEqual(num_users_first_pw_change, num_users_second_pw_change)

        # The django password hash shall have changed.
        self.assertNotEqual(django_hash_prior, django_hash_posterior)

    def test_saving_additional_user_data_shall_not_change_database_role(self):
        name = "John Doe"
        password = "12345"

        User.objects.create(username=name, password=password, has_dbuser=True)

        user = User.objects.filter(username=name).first()

        # Assert that the following code does not raise an error
        user.last_login = datetime(2022, 1, 23, 12, 20, tzinfo=timezone.utc)
        user.save(update_fields=["last_login"])

        # Additional information shall be saved (make sure, it is not simply ignored).
        testuser = User.objects.get(pk=user.pk)
        self.assertIsNotNone(testuser)
        self.assertEqual(testuser.last_login, user.last_login)

    def test_queryset_delete_shall_delete_the_corresponding_users_in_the_database(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        name2 = "Max Mustermann"
        name3 = "Jean Dupont"
        password = "12345"

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_prior = len(cursor.fetchall())

        User.objects.create(username=name1, password=password, has_dbuser=True)
        User.objects.create(username=name2, password=password, has_dbuser=True)
        User.objects.create(username=name3, password=password, has_dbuser=True)

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_creation = len(cursor.fetchall())

        self.assertEqual(num_users_prior + 3, num_users_after_creation)

        User.objects.all().delete()

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_deletion = len(cursor.fetchall())

        self.assertEqual(num_users_after_deletion, num_users_prior)

    def test_no_user_shall_be_created_if_has_dbuser_is_false(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        name2 = "Max Mustermann"
        name3 = "Jean Dupont"
        password = "12345"

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_prior = len(cursor.fetchall())

        User.objects.create(username=name1, password=password, has_dbuser=True)
        User.objects.create(username=name2, password=password, has_dbuser=False)
        User.objects.create(username=name3, password=password, has_dbuser=True)

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_creation = len(cursor.fetchall())

        self.assertEqual(num_users_prior + 2, num_users_after_creation)

        User.objects.all().delete()

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_deletion = len(cursor.fetchall())

        self.assertEqual(num_users_after_deletion, num_users_prior)

    def test_bulk_create_user_shall_create_multiple_users(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        name2 = "Max Mustermann"
        name3 = "Jean Dupont"
        password = "12345"

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_prior = len(cursor.fetchall())

        users = [User(username=name1, password=password), User(username=name2, password=password), User(username=name3, password=password)]
        User.objects.bulk_create(users)        

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_creation = len(cursor.fetchall())

        self.assertEqual(num_users_prior + 3, num_users_after_creation)

        User.objects.all().delete()

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_deletion = len(cursor.fetchall())

        self.assertEqual(num_users_after_deletion, num_users_prior)

    def test_setting_has_dbuser_to_false_shall_remove_db_user(self):
        cursor = connection.cursor()
        name1 = "John Doe"
        password = "12345"

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_prior = len(cursor.fetchall())

        user = User.objects.create(username=name1, password=password, has_dbuser=True)

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_creation = len(cursor.fetchall())

        self.assertEqual(num_users_prior + 1, num_users_after_creation)

        user.has_dbuser = False
        user.save()

        cursor.execute(sql.SQL("SELECT * FROM pg_roles"))
        num_users_after_deletion = len(cursor.fetchall())

        self.assertEqual(num_users_after_deletion, num_users_prior)
