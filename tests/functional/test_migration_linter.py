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

from django_migration_linter import MigrationLinter
from tests import fixtures


class BackwardcompatibilityDetectionTest(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        return super(
            BackwardcompatibilityDetectionTest, self).setUp(*args, **kwargs)

    def test_create_table_with_not_null_column(self):
        linter = MigrationLinter(
            fixtures.CREATE_TABLE_WITH_NOT_NULL_COLUMN_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertFalse(has_errors)

    def test_detect_adding_not_null_column(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertTrue(has_errors)

    def test_detect_drop_column(self):
        linter = MigrationLinter(
            fixtures.DROP_COLUMN_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertTrue(has_errors)

    def test_detect_rename_column(self):
        linter = MigrationLinter(
            fixtures.RENAME_COLUMN_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertTrue(has_errors)

    def test_detect_rename_table(self):
        linter = MigrationLinter(
            fixtures.RENAME_TABLE_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertTrue(has_errors)

    def test_accept_not_null_column_followed_by_adding_default(self):
        linter = MigrationLinter(
            fixtures.ADD_NOT_NULL_COLUMN_FOLLOWED_BY_DEFAULT_PROJECT)
        has_errors = linter.lint_migrations()
        self.assertFalse(has_errors)

    def test_specify_git_hash(self):
        linter = MigrationLinter(
            fixtures.MULTI_COMMIT_PROJECT,
            commit_id=None)
        has_errors = linter.lint_migrations()
        self.assertTrue(has_errors)

        linter = MigrationLinter(
            fixtures.MULTI_COMMIT_PROJECT,
            commit_id='44330921696018f8f1480df897b38310549982cb')
        has_errors = linter.lint_migrations()
        self.assertFalse(has_errors)

        linter = MigrationLinter(
            fixtures.MULTI_COMMIT_PROJECT,
            commit_id='tag1')
        has_errors = linter.lint_migrations()
        self.assertFalse(has_errors)
