from django.test import TestCase
from django.contrib.auth.models import Permission

from serverside import utils


class TestPermissions(TestCase):
    def test_create_permissions_shall_create_permissions_for_all_models(self):
        models = utils.get_all_models(True, False)
        self.assertGreater(len(models), 1)

        for m in models:
            codename = utils.get_permission_codename("select", m)
            self.assertIsNotNone(Permission.objects.filter(codename=codename))

    