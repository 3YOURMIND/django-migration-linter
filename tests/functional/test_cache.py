from __future__ import annotations

import os
import unittest
import unittest.mock as mock

from django.conf import settings
from django.db.migrations import Migration

from django_migration_linter import (
    IgnoreMigration,
    Issue,
    MigrationLinter,
    analyse_sql_statements,
    get_migration_abspath,
)


class OperationsIgnoreMigration(Migration):
    operations = [IgnoreMigration()]


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        self.test_project_path = os.path.dirname(settings.BASE_DIR)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_create_table", "app_add_not_null_column"),
            Migration("0002_add_new_not_null_field", "app_add_not_null_column"),
        ],
    )
    def test_cache_normal(self, *args):
        linter = MigrationLinter(self.test_project_path, database="mysql")
        linter.old_cache.clear()
        linter.old_cache.save()

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(2, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("OK", cache["ab2eef5ceb020d0e6eaa42dda2a754c5"]["result"])
        self.assertEqual("ERR", cache["52000d9d2c43dfda982945000dc6ba54"]["result"])
        self.assertListEqual(
            [
                Issue(
                    code="NOT_NULL",
                    message="NOT NULL constraint on columns",
                ),
            ],
            cache["52000d9d2c43dfda982945000dc6ba54"]["errors"],
        )

        # Start the Linter again -> should use cache now.
        linter = MigrationLinter(self.test_project_path, database="mysql")

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            analyse_sql_statements_mock.assert_not_called()

        self.assertTrue(linter.has_errors)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_create_table", "app_add_not_null_column"),
            Migration("0002_add_new_not_null_field", "app_add_not_null_column"),
        ],
    )
    def test_cache_different_databases(self, *args):
        linter = MigrationLinter(self.test_project_path, database="mysql")
        linter.old_cache.clear()
        linter.old_cache.save()

        linter = MigrationLinter(self.test_project_path, database="sqlite")
        linter.old_cache.clear()
        linter.old_cache.save()

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(2, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("OK", cache["ab2eef5ceb020d0e6eaa42dda2a754c5"]["result"])
        self.assertEqual("ERR", cache["52000d9d2c43dfda982945000dc6ba54"]["result"])
        self.assertListEqual(
            [
                Issue(
                    code="NOT_NULL",
                    message="NOT NULL constraint on columns",
                ),
            ],
            cache["52000d9d2c43dfda982945000dc6ba54"]["errors"],
        )

        # Start the Linter again but with different database, should not be the same cache
        linter = MigrationLinter(self.test_project_path, database="mysql")

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(2, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("OK", cache["ab2eef5ceb020d0e6eaa42dda2a754c5"]["result"])
        self.assertEqual("ERR", cache["52000d9d2c43dfda982945000dc6ba54"]["result"])
        self.assertListEqual(
            [
                Issue(
                    code="NOT_NULL",
                    message="NOT NULL constraint on columns",
                ),
            ],
            cache["52000d9d2c43dfda982945000dc6ba54"]["errors"],
        )

        self.assertTrue(linter.has_errors)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_initial", "app_ignore_migration"),
            OperationsIgnoreMigration("0002_ignore_migration", "app_ignore_migration"),
        ],
    )
    def test_cache_ignored(self, *args):
        linter = MigrationLinter(self.test_project_path, ignore_name_contains="0001")
        linter.old_cache.clear()
        linter.old_cache.save()

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            analyse_sql_statements_mock.assert_not_called()

        cache = linter.new_cache
        cache.load()

        self.assertFalse(cache)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0002_add_new_not_null_field", "app_add_not_null_column")
        ],
    )
    def test_cache_modified(self, *args):
        linter = MigrationLinter(self.test_project_path, database="mysql")
        linter.old_cache.clear()
        linter.old_cache.save()

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(1, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("ERR", cache["52000d9d2c43dfda982945000dc6ba54"]["result"])

        # Get the content of the migration file and mock the open call to append
        # some content to change the hash
        migration_path = get_migration_abspath(
            "app_add_not_null_column", "0002_add_new_not_null_field"
        )
        with open(migration_path, "rb") as f:
            file_content = f.read()
        file_content += b"# test comment"

        linter = MigrationLinter(self.test_project_path)
        with mock.patch(
            "django_migration_linter.migration_linter.open",
            mock.mock_open(read_data=file_content),
        ):
            with mock.patch(
                "django_migration_linter.migration_linter.analyse_sql_statements",
                wraps=analyse_sql_statements,
            ) as analyse_sql_statements_mock:
                linter.lint_all_migrations()
                self.assertEqual(1, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertNotIn("52000d9d2c43dfda982945000dc6ba54", cache)
        self.assertEqual(1, len(cache))
        self.assertEqual("ERR", cache["edeb40ecc1f5550ebef876c8e8ca093d"]["result"])

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_create_table", "app_add_not_null_column"),
            Migration("0002_add_new_not_null_field", "app_add_not_null_column"),
        ],
    )
    def test_ignore_cached_migration(self, *args):
        linter = MigrationLinter(self.test_project_path, database="mysql")
        linter.old_cache.clear()
        linter.old_cache.save()

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(2, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("OK", cache["ab2eef5ceb020d0e6eaa42dda2a754c5"]["result"])
        self.assertEqual("ERR", cache["52000d9d2c43dfda982945000dc6ba54"]["result"])
        self.assertListEqual(
            [
                Issue(
                    code="NOT_NULL",
                    message="NOT NULL constraint on columns",
                ),
            ],
            cache["52000d9d2c43dfda982945000dc6ba54"]["errors"],
        )

        # Start the Linter again -> should use cache now but ignore the erroneous
        linter = MigrationLinter(
            self.test_project_path,
            ignore_name_contains="0002_add_new_not_null_field",
            database="mysql",
        )

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            analyse_sql_statements_mock.assert_not_called()

        self.assertFalse(linter.has_errors)

        cache = linter.new_cache
        cache.load()
        self.assertEqual(1, len(cache))
        self.assertEqual("OK", cache["ab2eef5ceb020d0e6eaa42dda2a754c5"]["result"])
