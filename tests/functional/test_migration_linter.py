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

from django_migration_linter import MigrationLinter
from tests import fixtures


class BaseBackwardCompatibilityDetection(object):
    def tearDown(self, *args, **kwargs):
        fixtures.clear_all_git_projects()
        super(
            BaseBackwardCompatibilityDetection,
            self).tearDown(*args, **kwargs)

    def _test_linter_finds_errors(self, path, commit_id=None):
        linter = MigrationLinter(path, database=self.DATABASE, no_cache=True)
        linter.lint_all_migrations(git_commit_id=commit_id)
        self.assertTrue(linter.has_errors)

    def _test_linter_finds_no_errors(self, path, commit_id=None):
        linter = MigrationLinter(path, database=self.DATABASE, no_cache=True)
        linter.lint_all_migrations(git_commit_id=commit_id)
        self.assertFalse(linter.has_errors)

    # *** Tests ***
    def test_create_table_with_not_null_column(self):
        test_project_path = fixtures.CREATE_TABLE_WITH_NOT_NULL_COLUMN_PROJECT
        self._test_linter_finds_no_errors(test_project_path)

    def test_detect_adding_not_null_column(self):
        test_project_path = fixtures.ADD_NOT_NULL_COLUMN_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_detect_drop_column(self):
        test_project_path = fixtures.DROP_COLUMN_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_detect_rename_column(self):
        test_project_path = fixtures.RENAME_COLUMN_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_detect_rename_table(self):
        test_project_path = fixtures.RENAME_TABLE_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_ignore_migration(self):
        test_project_path = fixtures.IGNORE_MIGRATION_PROJECT
        self._test_linter_finds_no_errors(test_project_path)

    def test_accept_not_null_column_followed_by_adding_default(self):
        test_project_path = \
            fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT_PROJECT
        self._test_linter_finds_no_errors(test_project_path)

    def test_detect_alter_column(self):
        test_project_path = fixtures.ALTER_COLUMN_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_no_specify_git_hash(self):
        test_project_path = fixtures.MULTI_COMMIT_PROJECT
        fixtures.prepare_git_project(test_project_path)
        self._test_linter_finds_errors(test_project_path, commit_id=None)

    def test_specify_git_hash_by_commit_hash(self):
        test_project_path = fixtures.MULTI_COMMIT_PROJECT
        fixtures.prepare_git_project(test_project_path)
        self._test_linter_finds_no_errors(
            test_project_path,
            commit_id='d7125d5f4f0cc9623f670a66c54f131acc50032d')

    #def test_specify_git_hash_by_tag(self):
    #    test_project_path = fixtures.MULTI_COMMIT_PROJECT
    #    fixtures.prepare_git_project(test_project_path)
    #    self._test_linter_finds_no_errors(test_project_path, commit_id='tag1')


class MySqlBackwardCompatibilityDetectionTest(unittest.TestCase, BaseBackwardCompatibilityDetection):
    DATABASE = "mysql"

class SqliteBackwardCompatibilityDetectionTest(unittest.TestCase, BaseBackwardCompatibilityDetection):
    DATABASE = "sqlite"

    def test_accept_not_null_column_followed_by_adding_default(self):
        test_project_path = \
            fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT_PROJECT
        self._test_linter_finds_errors(test_project_path)

    def test_specify_git_hash_by_commit_hash(self):
        test_project_path = fixtures.MULTI_COMMIT_PROJECT
        fixtures.prepare_git_project(test_project_path)
        self._test_linter_finds_errors(
            test_project_path,
            commit_id='d7125d5f4f0cc9623f670a66c54f131acc50032d')


class PostgresqlBackwardCompatibilityDetectionTest(unittest.TestCase, BaseBackwardCompatibilityDetection):
    DATABASE = "postgresql"
