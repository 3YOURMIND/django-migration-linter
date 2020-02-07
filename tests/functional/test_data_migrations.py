import os
import unittest

from django.conf import settings

from django_migration_linter import MigrationLinter
from tests import fixtures


class DataMigrationDetectionTestCase(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.test_project_path = os.path.dirname(settings.BASE_DIR)
        self.linter = MigrationLinter(
            self.test_project_path, include_apps=fixtures.DATA_MIGRATIONS,
        )

    def test_reverse_data_migration(self):
        self.assertEqual(0, self.linter.nb_warnings)
        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0002_missing_reverse")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertFalse(self.linter.has_errors)

    def test_reverse_data_migration_ignore(self):
        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertFalse(self.linter.has_errors)

    def test_exclude_warning_from_test(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            exclude_migration_tests=("REVERSIBLE_DATA_MIGRATION",),
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0002_missing_reverse")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_valid)
        self.assertFalse(self.linter.has_errors)

    def test_warnings_as_errors(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            warnings_as_errors=True,
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_erroneous)
        self.assertTrue(self.linter.has_errors)
