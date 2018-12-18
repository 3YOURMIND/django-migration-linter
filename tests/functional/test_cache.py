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
import os
import shutil
import tempfile
import unittest
from unittest import mock

from django_migration_linter.utils import get_default_cache_file
from tests import fixtures

from django_migration_linter import MigrationLinter
from tests.fixtures import ADD_NOT_NULL_COLUMN_PROJECT


class CacheTest(unittest.TestCase):
    MIGRATION_FILE = os.path.join(ADD_NOT_NULL_COLUMN_PROJECT, 'test_app', 'migrations', '0001_create_table.py')
    fd, temp_path = tempfile.mkstemp()

    def setUp(self):
        shutil.copy2(self.MIGRATION_FILE, self.temp_path)

    def tearDown(self):
        shutil.copy2(self.temp_path, self.MIGRATION_FILE)
        os.remove(self.temp_path)

    def test_cache_normal(self):
        if os.path.exists(get_default_cache_file('test_project_add_not_null_column')):
            os.remove(get_default_cache_file('test_project_add_not_null_column'))
        linter = MigrationLinter(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)
        linter.lint_all_migrations()
        cache = linter.get_cache()
        self.assertEqual(cache['hash']['result'], 'OK')
        self.assertEqual(cache['hashERR']['result'], 'ERR')
        self.assertDictEqual(cache['hashERR']['errors'], ...)

        with mock.patch(
                'subprocess.Popen'
        ) as popen_mock:
            linter.lint_all_migrations()
        self.assertEqual(popen_mock.call_count, 2)

        with mock.patch(
                'subprocess.Popen'
        ) as popen_mock:
            linter.lint_all_migrations()

        self.assertEqual(popen_mock.call_count, 0)
        self.assertFalse(linter.has_errors())

    def test_cache_ignored(self):
        pass

    def test_cache_modified(self):
        if os.path.exists(get_default_cache_file('test_project_add_not_null_column')):
            os.remove(get_default_cache_file('test_project_add_not_null_column'))
        linter = MigrationLinter(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)
        linter.lint_all_migrations()
        cache = linter.get_cache()
        self.assertEqual(cache['hash']['result'], 'OK')
        self.assertEqual(cache['hashERR']['result'], 'ERR')
        self.assertDictEqual(cache['hashERR']['errors'], ...)

        with open( self.MIGRATION_FILE, "a") as f:
            f.write("# modification at the end of the file\n")

        linter.lint_all_migrations()
        cache = linter.get_cache()

        self.assertNotIn('hash', cache)
        self.assertEqual(cache['newhash']['result'], 'OK')



