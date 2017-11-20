# Copyright 2017 3YOURMIND GmbH

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

from tests import fixtures
from django_migration_linter import MigrationLinter, valid_folder


class UtilityFunctionTest(unittest.TestCase):
    def tearDown(self, *args, **kwargs):
        #fixtures.clear_all_git_projects()
        super(
            UtilityFunctionTest,
            self).tearDown(*args, **kwargs)

    def test_split_migration_path(self):
        input_path = 'apps/the_app/migrations/0001_stuff.py'
        app, mig = MigrationLinter._split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')

    def test_split_migration_path_2(self):
        input_path = 'the_app/migrations/0001_stuff.py'
        app, mig = MigrationLinter._split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')

    def test_detect_valid_folder(self):
        test_project_path = fixtures.MULTI_COMMIT_PROJECT
        fixtures.prepare_git_project(test_project_path)
        self.assertTrue(valid_folder(test_project_path))

    def test_detect_not_django_project(self):
        test_project_path = fixtures.NOT_DJANGO_GIT_PROJECT
        fixtures.prepare_git_project(test_project_path)
        self.assertFalse(valid_folder(test_project_path))

    def test_detect_not_git_project(self):
        self.assertFalse(valid_folder(fixtures.NOT_GIT_DJANGO_PROJECT))
