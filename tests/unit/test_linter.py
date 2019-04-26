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

import unittest

from django.db.migrations import Migration

from django_migration_linter import MigrationLinter


class LinterFunctionsTestCase(unittest.TestCase):
    def test_get_sql(self):
        linter = MigrationLinter()
        sql_statements = linter.get_sql("app_add_not_null_column", "0001")
        self.assertEqual(len(sql_statements), 6)
        self.assertEqual(sql_statements[0], "BEGIN;")
        self.assertEqual(sql_statements[-1], "COMMIT;")

    def test_has_errors(self):
        linter = MigrationLinter()
        self.assertFalse(linter.has_errors)

        m = Migration("0001_create_table", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertFalse(linter.has_errors)

        m = Migration("0002_add_new_not_null_field", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertTrue(linter.has_errors)

        m = Migration("0001_create_table", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertTrue(linter.has_errors)

    def test_ignore_migration_include_apps(self):
        linter = MigrationLinter(include_apps=("app_add_not_null_column",))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0001"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002"))
        self.assertFalse(
            linter.should_ignore_migration("app_add_not_null_column", "0001")
        )

    def test_ignore_migration_exclude_apps(self):
        linter = MigrationLinter(exclude_apps=("app_add_not_null_column",))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001"))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0002"))
        self.assertTrue(
            linter.should_ignore_migration("app_add_not_null_column", "0001")
        )

    def test_ignore_migration_name_contains(self):
        linter = MigrationLinter(ignore_name_contains="foo")
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_ignore_migration_full_name(self):
        linter = MigrationLinter(ignore_name=("0002_foo",))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_gather_all_migrations(self):
        linter = MigrationLinter()
        migrations = linter._gather_all_migrations()
        self.assertGreater(len(list(migrations)), 1)
