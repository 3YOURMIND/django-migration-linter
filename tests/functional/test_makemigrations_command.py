import os
import shutil
import sys
from contextlib import contextmanager
from importlib import import_module

if sys.version_info >= (3, 3):
    import unittest.mock as mock
else:
    import mock

if sys.version_info.major >= 3:
    import tempfile
    from io import StringIO as StringIO
else:
    from backports import tempfile
    from io import BytesIO as StringIO

from django.apps import apps
from django.conf import settings
from django.core.management import call_command
from django.test import TransactionTestCase
from django.test.utils import extend_sys_path, override_settings
from django.utils.module_loading import module_dir

MAKEMIGRATIONS_INSTALLED_APPS = settings.INSTALLED_APPS + [
    "tests.test_project.makemigrations_correct_migration_missing",
    "tests.test_project.makemigrations_backward_incompatible_migration_missing",
]


@override_settings(INSTALLED_APPS=MAKEMIGRATIONS_INSTALLED_APPS)
class BaseMakeMigrationsTestCase(TransactionTestCase):
    @contextmanager
    def temporary_migration_module(self, app_label="migrations", module=None):
        """
        Shamelessly copied from Django.
        See django.tests.migrations.test_base.MigrationTestBase.temporary_migration_module

        Allows testing management commands in a temporary migrations module.

        Wrap all invocations to makemigrations and squashmigrations with this
        context manager in order to avoid creating migration files in your
        source tree inadvertently.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            target_dir = tempfile.mkdtemp(dir=temp_dir)
            with open(os.path.join(target_dir, "__init__.py"), "w"):
                pass
            target_migrations_dir = os.path.join(target_dir, "migrations")

            if module is None:
                module = apps.get_app_config(app_label).name + ".migrations"

            try:
                source_migrations_dir = module_dir(import_module(module))
            except (ImportError, ValueError):
                pass
            else:
                shutil.copytree(source_migrations_dir, target_migrations_dir)

            with extend_sys_path(temp_dir):
                new_module = os.path.basename(target_dir) + ".migrations"
                with self.settings(MIGRATION_MODULES={app_label: new_module}):
                    yield target_migrations_dir


class MakeMigrationsCorrectTestCase(BaseMakeMigrationsTestCase):
    available_apps = [
        "django_migration_linter",
        "tests.test_project.makemigrations_correct_migration_missing",
    ]
    databases = {"default", "postgresql"}

    def test_correct_linted_makemigrations(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_correct_migration_missing"
        ) as migration_dir:
            call_command("makemigrations", lint=True, database="postgresql", stdout=out)
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertTrue(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Linting for 'makemigrations_correct_migration_missing':", output)

    @override_settings(MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS=True)
    def test_correct_linted_makemigrations_using_settings(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_correct_migration_missing"
        ) as migration_dir:
            call_command("makemigrations", database="postgresql", stdout=out)
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertTrue(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Linting for 'makemigrations_correct_migration_missing':", output)

    def test_no_linting_when_no_option(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_correct_migration_missing"
        ) as migration_dir:
            call_command("makemigrations", database="postgresql", stdout=out)
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertTrue(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertNotIn("Linting", output)

    def test_correct_linted_makemigrations_dry_run(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_correct_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations",
                lint=True,
                database="postgresql",
                dry_run=True,
                stdout=out,
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertFalse(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertNotIn("Linting", output)


@override_settings(MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS=True)
class MakeMigrationsBackwardIncompatibleTestCase(BaseMakeMigrationsTestCase):
    available_apps = [
        "django_migration_linter",
        "tests.test_project.makemigrations_backward_incompatible_migration_missing",
    ]
    databases = {"default", "sqlite", "mysql", "postgresql"}

    def test_backward_incompatible_migration_postgresql(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_backward_incompatible_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations", interactive=False, database="postgresql", stdout=out
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertFalse(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Deleted", output)

    def test_backward_incompatible_migration_mysql(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_backward_incompatible_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations", interactive=False, database="mysql", stdout=out
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertFalse(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Deleted", output)

    def test_backward_incompatible_migration_sqlite(self):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_backward_incompatible_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations", interactive=False, database="sqlite", stdout=out
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertFalse(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Deleted", output)

    @mock.patch("django.db.migrations.questioner.input", return_value="yes")
    def test_backward_incompatible_migration_interactive_keep_migration(self, *args):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_backward_incompatible_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations", interactive=True, database="postgresql", stdout=out
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertTrue(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertNotIn("Deleted", output)

    @mock.patch("django.db.migrations.questioner.input", return_value="no")
    def test_backward_incompatible_migration_interactive_delete_migration(self, *args):
        out = StringIO()
        with self.temporary_migration_module(
            app_label="makemigrations_backward_incompatible_migration_missing"
        ) as migration_dir:
            call_command(
                "makemigrations", interactive=True, database="postgresql", stdout=out
            )
            new_migration_file = os.path.join(migration_dir, "0002_a_new_field.py")
            self.assertFalse(os.path.exists(new_migration_file))
        output = out.getvalue()
        self.assertIn("Deleted", output)
