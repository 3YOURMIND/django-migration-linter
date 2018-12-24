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
import pprint
import shutil
import tempfile
import unittest
import sys

from tests import fixtures

from django_migration_linter import MigrationLinter, Cache, DEFAULT_CACHE_PATH

if sys.version_info >= (3, 3):
    import unittest.mock as mock
else:
    import mock


class CacheTest(unittest.TestCase):
    MIGRATION_FILE = os.path.join(fixtures.ALTER_COLUMN_PROJECT, 'test_app', 'migrations', '0001_initial.py')
    fd, temp_path = tempfile.mkstemp()

    def setUp(self):
        shutil.copy2(self.MIGRATION_FILE, self.temp_path)

    def tearDown(self):
        shutil.copy2(self.temp_path, self.MIGRATION_FILE)
        os.remove(self.temp_path)

    def test_cache_normal(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_project_add_not_null_column.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        linter = MigrationLinter(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)

        with mock.patch.object(MigrationLinter, 'get_sql', wraps=linter.get_sql)as sql_mock:
            linter.lint_all_migrations()
            self.assertEqual(sql_mock.call_count, 2)

        cache = Cache(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT,
            DEFAULT_CACHE_PATH
        )
        cache.load()

        self.assertEqual(cache['3ef74e7f3e53e273e2fc95379248d58d']['result'], 'OK')
        self.assertEqual(cache['e1e312b6d08ecbe017c25c58fc2be257']['result'], 'ERR')
        self.assertListEqual(
            cache['e1e312b6d08ecbe017c25c58fc2be257']['errors'],
            [{'err_msg': 'RENAMING tables', 'code': 'RENAME_TABLE', 'table': None, 'column': None}]
        )

        # Start the Linter again -> should use cache now.
        linter = MigrationLinter(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)

        with mock.patch.object(MigrationLinter, 'get_sql', wraps=linter.get_sql) as sql_mock:
            linter.lint_all_migrations()
            self.assertEqual(sql_mock.call_count, 0)

        self.assertTrue(linter.has_errors)

    def test_cache_ignored(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_project_ignore_migration.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        linter = MigrationLinter(fixtures.IGNORE_MIGRATION_PROJECT)

        with mock.patch.object(MigrationLinter, 'get_sql', wraps=linter.get_sql) as sql_mock:
            linter.lint_all_migrations()
            self.assertEqual(sql_mock.call_count, 2)

        cache = Cache(
            fixtures.IGNORE_MIGRATION_PROJECT,
            DEFAULT_CACHE_PATH
        )
        cache.load()

        self.assertEqual(cache['63230606af0eccaef7f1f78c537c624c']['result'], 'OK')
        self.assertEqual(cache['5c5ca1780a9f28439c1defc1f32af894']['result'], 'IGNORE')

        # Start the Linter again -> should use cache now.
        linter = MigrationLinter(fixtures.IGNORE_MIGRATION_PROJECT)

        with mock.patch.object(MigrationLinter, 'get_sql', wraps=linter.get_sql) as sql_mock:
            linter.lint_all_migrations()
            self.assertEqual(sql_mock.call_count, 0)

    def test_cache_ignored_command_line(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_project_ignore_migration.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        linter = MigrationLinter(fixtures.IGNORE_MIGRATION_PROJECT,
                                 ignore_name_contains='0001')

        with mock.patch.object(MigrationLinter, 'get_sql', wraps=linter.get_sql) as sql_mock:
            linter.lint_all_migrations()
            self.assertEqual(sql_mock.call_count, 1)

        cache = Cache(
            fixtures.IGNORE_MIGRATION_PROJECT,
            DEFAULT_CACHE_PATH
        )
        cache.load()

        self.assertNotIn('63230606af0eccaef7f1f78c537c624c', cache)
        self.assertEqual(cache['5c5ca1780a9f28439c1defc1f32af894']['result'], 'IGNORE')

    def test_cache_modified(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_project_alter_column.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        linter = MigrationLinter(fixtures.ALTER_COLUMN_PROJECT)
        linter.lint_all_migrations()
        cache = Cache(
            fixtures.ALTER_COLUMN_PROJECT,
            DEFAULT_CACHE_PATH
        )
        cache.load()

        self.assertEqual(cache['8589aa107b6da296c4b49cd2681d2230']['result'], 'OK',
                         'If this fails, tearDown might have failed to remove '
                         'the modification from tests/test_project_fixtures/'
                         'test_project_alter_column/test_app/migrations/0001_initial.py'
                         )
        self.assertEqual(cache['8f54c4a434cfaa9838e8ca12eb988255']['result'], 'ERR')
        self.assertListEqual(
            cache['8f54c4a434cfaa9838e8ca12eb988255']['errors'],
            [{u'err_msg': u'ALTERING columns (Could be backward compatible. '
                          u'You may ignore this migration.)',
              u'code': u'ALTER_COLUMN',
              u'table': u'test_app_a',
              u'column': None}
             ]
        )

        # Modify migration
        with open(self.MIGRATION_FILE, "a") as f:
            f.write("# modification at the end of the file\n")

        # Start the Linter again -> Cache should look different now
        linter = MigrationLinter(fixtures.ALTER_COLUMN_PROJECT)
        linter.lint_all_migrations()
        cache = Cache(
            fixtures.ALTER_COLUMN_PROJECT,
            DEFAULT_CACHE_PATH
        )
        cache.load()

        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(cache)

        self.assertNotIn('8589aa107b6da296c4b49cd2681d2230', cache)
        self.assertEqual(cache['44f9d6d019d6f158946c2819b2bd8bf9']['result'], 'OK')
