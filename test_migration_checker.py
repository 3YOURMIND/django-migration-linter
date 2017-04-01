import unittest

import checker


class CheckerTest(unittest.TestCase):
    def test_split_migration_path(self):
        input_path = 'apps/the_app/migrations/0001_stuff.py'
        app, mig = checker.split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')

    def test_split_migration_path_2(self):
        input_path = 'the_app/migrations/0001_stuff.py'
        app, mig = checker.split_migration_path(input_path)
        self.assertEqual(app, 'the_app')
        self.assertEqual(mig, '0001_stuff')
