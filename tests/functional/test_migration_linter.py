from __future__ import annotations

import os
import unittest

from django.conf import settings
from django.core.management import call_command

from django_migration_linter import MigrationLinter
from tests import fixtures


class BaseBackwardCompatibilityDetection:
    def setUp(self, *args, **kwargs):
        self.database = next(iter(self.databases))
        self.test_project_path = os.path.dirname(settings.BASE_DIR)
        call_command(
            "migrate",
            "app_unique_together",
            "0002",
            database=self.database,
        )
        self.addCleanup(
            call_command,
            "migrate",
            "app_unique_together",
            database=self.database,
        )
        return super().setUp(*args, **kwargs)

    def _test_linter_finds_errors(self, app=None, commit_id=None):
        linter = self._launch_linter(app, commit_id)
        self.assertTrue(linter.has_errors)
        self.assertNotEqual(linter.nb_valid + linter.nb_erroneous, 0)

    def _test_linter_finds_no_errors(self, app=None, commit_id=None):
        linter = self._launch_linter(app, commit_id)
        self.assertFalse(linter.has_errors)
        self.assertNotEqual(linter.nb_valid + linter.nb_erroneous, 0)

    def _launch_linter(self, app=None, commit_id=None):
        linter = MigrationLinter(
            self.test_project_path,
            database=self.database,
            no_cache=True,
        )
        linter.lint_all_migrations(app_label=app, git_commit_id=commit_id)
        return linter

    # *** Tests ***
    def test_create_table_with_not_null_column(self):
        app = fixtures.CREATE_TABLE_WITH_NOT_NULL_COLUMN
        self._test_linter_finds_no_errors(app)

    def test_detect_adding_not_null_column(self):
        app = fixtures.ADD_NOT_NULL_COLUMN
        self._test_linter_finds_errors(app)

    def test_detect_make_column_not_null_with_django_default(self):
        app = fixtures.MAKE_NOT_NULL_WITH_DJANGO_DEFAULT
        self._test_linter_finds_errors(app)

    def test_detect_make_column_not_null_with_lib_default(self):
        app = fixtures.MAKE_NOT_NULL_WITH_LIB_DEFAULT
        self._test_linter_finds_no_errors(app)

    def test_detect_drop_column(self):
        app = fixtures.DROP_COLUMN
        self._test_linter_finds_errors(app)

    def test_detect_drop_table(self):
        app = fixtures.DROP_TABLE
        self._test_linter_finds_errors(app)

    def test_detect_rename_column(self):
        app = fixtures.RENAME_COLUMN
        self._test_linter_finds_errors(app)

    def test_detect_rename_table(self):
        app = fixtures.RENAME_TABLE
        self._test_linter_finds_errors(app)

    def test_ignore_migration(self):
        app = fixtures.IGNORE_MIGRATION
        self._test_linter_finds_no_errors(app)

    def test_accept_not_null_column_followed_by_adding_default(self):
        app = fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT
        self._test_linter_finds_no_errors(app)

    def test_detect_alter_column(self):
        app = fixtures.ALTER_COLUMN
        self._test_linter_finds_no_errors(app)

    def test_drop_unique_together(self):
        app = fixtures.DROP_UNIQUE_TOGETHER
        self._test_linter_finds_errors(app)

    def test_accept_alter_column_drop_not_null(self):
        app = fixtures.ALTER_COLUMN_DROP_NOT_NULL
        self._test_linter_finds_no_errors(app)

    def test_accept_adding_manytomany_field(self):
        app = fixtures.ADD_MANYTOMANY_FIELD
        self._test_linter_finds_no_errors(app)

    def test_with_git_ref(self):
        self._test_linter_finds_errors(commit_id="v0.1.4")

    def test_failing_get_sql(self):
        call_command("migrate", "app_unique_together", database=self.database)

        linter = MigrationLinter(database=self.database)
        with self.assertRaises(ValueError):
            linter.get_sql("app_unique_together", "0003")


class SqliteBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["sqlite"]

    def test_accept_not_null_column_followed_by_adding_default(self):
        app = fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT
        self._test_linter_finds_errors(app)

    def test_detect_make_column_not_null_with_django_default(self):
        app = fixtures.MAKE_NOT_NULL_WITH_DJANGO_DEFAULT
        self._test_linter_finds_errors(app)

    def test_detect_make_column_not_null_with_lib_default(self):
        # The 'django-add-default-value' doesn't handle sqlite correctly
        app = fixtures.MAKE_NOT_NULL_WITH_LIB_DEFAULT
        self._test_linter_finds_errors(app)


class MySqlBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["mysql"]


class PostgresqlBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["postgresql"]

    def test_detect_alter_column(self):
        app = fixtures.ALTER_COLUMN
        self._test_linter_finds_errors(app)

    def test_create_index_exclusive(self):
        linter = self._launch_linter(fixtures.CREATE_INDEX_EXCLUSIVE)
        self.assertFalse(linter.has_errors)
        self.assertTrue(linter.nb_warnings)
