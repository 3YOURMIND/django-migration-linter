import unittest
import tempfile

from django.db.migrations import Migration

from django_migration_linter import MigrationLinter


class LinterFunctionsTestCase(unittest.TestCase):
    def test_get_sql(self):
        linter = MigrationLinter()
        sql_statements = linter.get_sql("app_add_not_null_column", "0001")
        self.assertEqual(len(sql_statements), 6)
        self.assertEqual(sql_statements[0], "BEGIN;")
        self.assertEqual(sql_statements[-1], "COMMIT;")

    def test_has_errors(self):
        linter = MigrationLinter(database="mysql")
        self.assertFalse(linter.has_errors)

        m = Migration("0001_create_table", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertFalse(linter.has_errors)

        m = Migration("0002_add_new_not_null_field", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertTrue(linter.has_errors)

        m = Migration("0001_create_table", "app_add_not_null_column")
        linter.lint_migration(m)
        self.assertTrue(linter.has_errors)

    def test_ignore_migration_include_apps(self):
        linter = MigrationLinter(include_apps=("app_add_not_null_column",))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0001"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002"))
        self.assertFalse(
            linter.should_ignore_migration("app_add_not_null_column", "0001")
        )

    def test_ignore_migration_exclude_apps(self):
        linter = MigrationLinter(exclude_apps=("app_add_not_null_column",))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001"))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0002"))
        self.assertTrue(
            linter.should_ignore_migration("app_add_not_null_column", "0001")
        )

    def test_ignore_migration_name_contains(self):
        linter = MigrationLinter(ignore_name_contains="foo")
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_ignore_migration_full_name(self):
        linter = MigrationLinter(ignore_name=("0002_foo",))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_gather_all_migrations(self):
        linter = MigrationLinter()
        migrations = linter._gather_all_migrations()
        self.assertGreater(len(list(migrations)), 1)

    def test_ignore_unapplied_migrations(self):
        linter = MigrationLinter(only_applied_migrations=True)
        linter.migration_loader.applied_migrations = {("app_correct", "0002_foo")}

        self.assertTrue(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertFalse(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_ignore_applied_migrations(self):
        linter = MigrationLinter(only_unapplied_migrations=True)
        linter.migration_loader.applied_migrations = {("app_correct", "0002_foo")}

        self.assertFalse(linter.should_ignore_migration("app_correct", "0001_initial"))
        self.assertTrue(linter.should_ignore_migration("app_correct", "0002_foo"))

    def test_exclude_migration_tests(self):
        m = Migration("0002_add_new_not_null_field", "app_add_not_null_column")

        linter = MigrationLinter(exclude_migration_tests=[], database="mysql")
        linter.lint_migration(m)
        self.assertTrue(linter.has_errors)

        linter = MigrationLinter(exclude_migration_tests=["NOT_NULL"], database="mysql")
        linter.lint_migration(m)
        self.assertFalse(linter.has_errors)

    def test_read_migrations_unknown_file(self):
        file_path = "unknown_file"
        with self.assertRaises(Exception):
            MigrationLinter.read_migrations_list(file_path)

    def test_read_migrations_no_file(self):
        migration_list = MigrationLinter.read_migrations_list(None)
        self.assertIsNone(migration_list)

    def test_read_migrations_empty_file(self):
        with tempfile.NamedTemporaryFile() as tmp:
            migration_list = MigrationLinter.read_migrations_list(tmp.name)
            self.assertEqual([], migration_list)

    def test_read_migrations_from_file(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
        tmp.write(
            "test_project/app_add_not_null_column/migrations/0001_create_table.py\n"
        )
        tmp.write("unknown\n")
        tmp.write(
            "test_project/app_add_not_null_column/migrations/0002_add_new_not_null_field.py\n"
        )
        tmp.close()
        migration_list = MigrationLinter.read_migrations_list(tmp.name)
        self.assertEqual(
            [
                ("app_add_not_null_column", "0001_create_table"),
                ("app_add_not_null_column", "0002_add_new_not_null_field"),
            ],
            migration_list,
        )

    def test_gather_migrations_with_list(self):
        linter = MigrationLinter()
        migrations = linter._gather_all_migrations(
            migrations_list=[
                ("app_add_not_null_column", "0001_create_table"),
                ("app_add_not_null_column", "0002_add_new_not_null_field"),
            ]
        )
        self.assertEqual(2, len(list(migrations)))
