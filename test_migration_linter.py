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
