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
