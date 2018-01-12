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


class TestMultipleLinters(unittest.TestCase):
    def test_multiple_linters(self):
        l1 = MigrationLinter(fixtures.ADD_NOT_NULL_COLUMN_PROJECT)
        l2 = MigrationLinter(fixtures.RENAME_COLUMN_PROJECT)
        l3 = MigrationLinter(fixtures.CORRECT_PROJECT)

        l1.lint_migration('test_app', '0002')
        l2.lint_migration('test_app', '0002')
        l3.lint_migration('test_app1', '0001')
        l3.lint_migration('test_app1', '0002')

        self.assertTrue(l1.has_errors)
        self.assertTrue(l2.has_errors)
        self.assertFalse(l3.has_errors)

        self.assertEqual(l1.nb_total, 1)
        self.assertEqual(l2.nb_total, 1)
        self.assertEqual(l3.nb_total, 2)
