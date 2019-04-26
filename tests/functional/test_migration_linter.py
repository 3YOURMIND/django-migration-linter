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

from django.conf import settings

from django_migration_linter import MigrationLinter
from tests import fixtures


class BaseBackwardCompatibilityDetection(object):
    def setUp(self, *args, **kwargs):
        self.test_project_path = os.path.dirname(settings.BASE_DIR)
        return super(BaseBackwardCompatibilityDetection, self).setUp(*args, **kwargs)

    def _test_linter_finds_errors(self, app=None, commit_id=None):
        linter = self._launch_linter(app, commit_id)
        self.assertTrue(linter.has_errors)
        self.assertNotEqual(linter.nb_valid + linter.nb_erroneous, 0)

    def _test_linter_finds_no_errors(self, app=None, commit_id=None):
        linter = self._launch_linter(app, commit_id)
        self.assertFalse(linter.has_errors)
        self.assertNotEqual(linter.nb_valid + linter.nb_erroneous, 0)

    def _launch_linter(self, app=None, commit_id=None):
        if app is not None:
            app = [app]

        linter = MigrationLinter(
            self.test_project_path,
            include_apps=app,
            database=next(iter(self.databases)),
            no_cache=True,
        )
        linter.lint_all_migrations(git_commit_id=commit_id)
        return linter

    # *** Tests ***
    def test_create_table_with_not_null_column(self):
        app = fixtures.CREATE_TABLE_WITH_NOT_NULL_COLUMN
        self._test_linter_finds_no_errors(app)

    def test_detect_adding_not_null_column(self):
        app = fixtures.ADD_NOT_NULL_COLUMN
        self._test_linter_finds_errors(app)

    def test_detect_drop_column(self):
        app = fixtures.DROP_COLUMN
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
        self._test_linter_finds_errors(app)

    def test_with_git_ref(self):
        self._test_linter_finds_errors(commit_id="v0.1.4")


class SqliteBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["sqlite"]

    def test_accept_not_null_column_followed_by_adding_default(self):
        app = fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT
        self._test_linter_finds_errors(app)


class MySqlBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["mysql"]


class PostgresqlBackwardCompatibilityDetectionTestCase(
    BaseBackwardCompatibilityDetection, unittest.TestCase
):
    databases = ["postgresql"]
