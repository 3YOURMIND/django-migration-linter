# Copyright 2019 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import unittest

from django.conf import settings
from django.db.migrations import Migration

from django_migration_linter import (
    MigrationLinter,
    analyse_sql_statements,
    get_migration_abspath,
)

if sys.version_info >= (3, 3):
    import unittest.mock as mock
else:
    import mock


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
        linter = MigrationLinter(self.test_project_path)
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

        self.assertEqual("OK", cache["4a3770a405738d457e2d23e17fb1f3aa"]["result"])
        self.assertEqual("ERR", cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["result"])
        self.assertListEqual(
            cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["errors"],
            [
                {
                    "err_msg": "RENAMING tables",
                    "code": "RENAME_TABLE",
                    "table": None,
                    "column": None,
                }
            ],
        )

        # Start the Linter again -> should use cache now.
        linter = MigrationLinter(self.test_project_path)

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

        self.assertEqual("OK", cache["4a3770a405738d457e2d23e17fb1f3aa"]["result"])
        self.assertEqual("ERR", cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["result"])
        self.assertListEqual(
            cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["errors"],
            [
                {
                    "err_msg": "RENAMING tables",
                    "code": "RENAME_TABLE",
                    "table": None,
                    "column": None,
                }
            ],
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

        self.assertEqual("OK", cache["4a3770a405738d457e2d23e17fb1f3aa"]["result"])
        self.assertEqual("ERR", cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["result"])
        self.assertListEqual(
            cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["errors"],
            [
                {
                    "err_msg": "NOT NULL constraint on columns",
                    "code": "NOT_NULL",
                    "table": "app_add_not_null_column_a",
                    "column": "new_not_null_field",
                }
            ],
        )

        self.assertTrue(linter.has_errors)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_initial", "app_ignore_migration"),
            Migration("0002_ignore_migration", "app_ignore_migration"),
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
            self.assertEqual(1, analyse_sql_statements_mock.call_count)

        cache = linter.new_cache
        cache.load()

        self.assertEqual("IGNORE", cache["0fab48322ba76570da1a3c193abb77b5"]["result"])

        # Start the Linter again -> should use cache now.
        linter = MigrationLinter(self.test_project_path)

        with mock.patch(
            "django_migration_linter.migration_linter.analyse_sql_statements",
            wraps=analyse_sql_statements,
        ) as analyse_sql_statements_mock:
            linter.lint_all_migrations()
            self.assertEqual(1, analyse_sql_statements_mock.call_count)

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0002_add_new_not_null_field", "app_add_not_null_column")
        ],
    )
    def test_cache_modified(self, *args):
        linter = MigrationLinter(self.test_project_path)
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

        self.assertEqual("ERR", cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["result"])

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

        self.assertNotIn("19fd3ea688fc05e2cc2a6e67c0b7aa17", cache)
        self.assertEqual(1, len(cache))
        self.assertEqual("ERR", cache["a25768641a0ad526fad199f97c303784"]["result"])

    @mock.patch(
        "django_migration_linter.MigrationLinter._gather_all_migrations",
        return_value=[
            Migration("0001_create_table", "app_add_not_null_column"),
            Migration("0002_add_new_not_null_field", "app_add_not_null_column"),
        ],
    )
    def test_ignore_cached_migration(self, *args):
        linter = MigrationLinter(self.test_project_path)
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

        self.assertEqual("OK", cache["4a3770a405738d457e2d23e17fb1f3aa"]["result"])
        self.assertEqual("ERR", cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["result"])
        self.assertListEqual(
            cache["19fd3ea688fc05e2cc2a6e67c0b7aa17"]["errors"],
            [
                {
                    "err_msg": "RENAMING tables",
                    "code": "RENAME_TABLE",
                    "table": None,
                    "column": None,
                }
            ],
        )

        # Start the Linter again -> should use cache now but ignore the erroneous
        linter = MigrationLinter(
            self.test_project_path, ignore_name_contains="0002_add_new_not_null_field"
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
        self.assertEqual("OK", cache["4a3770a405738d457e2d23e17fb1f3aa"]["result"])
