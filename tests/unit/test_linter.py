# Copyright 2018 3YOURMIND GmbH

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

from django_migration_linter import MigrationLinter
from tests import fixtures


class TestLinterFunctions(unittest.TestCase):
    def test_get_sql(self):
        project_path = fixtures.ADD_NOT_NULL_COLUMN_PROJECT
        linter = MigrationLinter(project_path)
        sql_statements = linter.get_sql('test_app', '0001')
        self.assertEqual(len(sql_statements), 6)
        self.assertEqual(sql_statements[0], 'BEGIN;')
        self.assertEqual(sql_statements[-1], 'COMMIT;')

    def test_has_errors(self):
        project_path = fixtures.MULTI_COMMIT_PROJECT
        linter = MigrationLinter(project_path)
        self.assertFalse(linter.has_errors)

        linter.lint_migration('test_app', '0001_create_table')
        self.assertFalse(linter.has_errors)

        linter.lint_migration('test_app', '0002_add_new_not_null_field')
        self.assertTrue(linter.has_errors)

        linter.lint_migration('test_app', '0001_create_table')
        self.assertTrue(linter.has_errors)

    def test_linter_creation(self):
        with self.assertRaises(ValueError):
            MigrationLinter('foo/')
        with self.assertRaises(ValueError):
            MigrationLinter('/dev/null')
        with self.assertRaises(ValueError):
            MigrationLinter(fixtures.NOT_DJANGO_GIT_PROJECT)

    def test_ignore_migration_include_apps(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT,
            include_apps=('test_app2',))
        self.assertTrue(linter.should_ignore_migration('test_app1', '0001'))
        self.assertFalse(linter.should_ignore_migration('test_app2', '0001'))

    def test_ignore_migration_exclude_apps(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT,
            exclude_apps=('test_app1',))
        self.assertTrue(linter.should_ignore_migration('test_app1', '0001'))
        self.assertFalse(linter.should_ignore_migration('test_app2', '0001'))

    def test_ignore_migration_name_contains(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT,
            ignore_name_contains='foo')
        self.assertTrue(linter.should_ignore_migration('test_app', '0001_foo'))
        self.assertFalse(linter.should_ignore_migration('test_app', '0002_bar'))

    def test_ignore_migration_full_name(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT,
            ignore_name=('0001_foo',))
        self.assertTrue(linter.should_ignore_migration('test_app', '0001_foo'))
        self.assertFalse(linter.should_ignore_migration('test_app', '0002_bar'))

    def test_gather_all_migrations(self):
        linter = MigrationLinter(fixtures.CORRECT_PROJECT)
        migrations = linter._gather_all_migrations()
        self.assertEqual(len(migrations), 3)
        self.assertEqual(migrations[0][0], 'test_app1')
        self.assertEqual(migrations[0][1], '0001_initial')
        self.assertEqual(migrations[1][0], 'test_app1')
        self.assertEqual(migrations[1][1], '0002_a_new_null_field')
        self.assertEqual(migrations[2][0], 'test_app2')
        self.assertEqual(migrations[2][1], '0001_foo')
