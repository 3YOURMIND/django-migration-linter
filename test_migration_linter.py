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

from migration_linter import MigrationLinter


class LinterTest(unittest.TestCase):
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
