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
import unittest

from tests import fixtures
from django_migration_linter.utils import is_django_project, is_directory, find_project_settings_module, \
    split_path, split_migration_path


class UtilityFunctionTest(unittest.TestCase):
    def test_detect_django_project(self):
        self.assertTrue(is_django_project(fixtures.ADD_NOT_NULL_COLUMN_PROJECT))

    def test_detect_not_django_project(self):
        self.assertFalse(is_django_project(fixtures._BASE_DIR))

    def test_detect_directory(self):
        self.assertTrue(is_directory(fixtures.ADD_NOT_NULL_COLUMN_PROJECT))

    def test_detect_not_directory(self):
        self.assertFalse(is_directory(
            os.path.join(fixtures.ADD_NOT_NULL_COLUMN_PROJECT, 'manage.py')))

    def test_find_project_settings_module_same_project_name(self):
        expected = 'test_project_add_not_null_column.settings'
        actual = find_project_settings_module(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)
        self.assertEqual(actual, expected)

    def test_find_project_settings_module_different_project_name(self):
        expected = 'test_project.settings'
        actual = find_project_settings_module(fixtures.CORRECT_PROJECT)
        self.assertEqual(actual, expected)

    def test_split_path(self):
        splitted = split_path('foo/bar/fuz.py')
        self.assertEqual(len(splitted), 3)
        self.assertEqual(splitted[0], 'foo')
        self.assertEqual(splitted[1], 'bar')
        self.assertEqual(splitted[2], 'fuz.py')

    def test_split_full_path(self):
        splitted = split_path('/foo/bar/fuz.py')
        self.assertEqual(len(splitted), 3)
        self.assertEqual(splitted[0], 'foo')
        self.assertEqual(splitted[1], 'bar')
        self.assertEqual(splitted[2], 'fuz.py')

    def test_split_folder_path(self):
        splitted = split_path('/foo/bar')
        self.assertEqual(len(splitted), 2)
        self.assertEqual(splitted[0], 'foo')
        self.assertEqual(splitted[1], 'bar')

    def test_split_migration_long_path(self):
        input_path = 'apps/the_app/migrations/0001_stuff.py'
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')

    def test_split_migration_path(self):
        input_path = 'the_app/migrations/0001_stuff.py'
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')

    def test_split_migration_full_path(self):
        input_path = '/home/user/djangostuff/apps/the_app/migrations/0001_stuff.py'
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')
