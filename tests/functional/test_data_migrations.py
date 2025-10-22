from __future__ import annotations

import os
import unittest

from django.conf import settings
from django.db import migrations

from django_migration_linter import MigrationLinter
from tests import fixtures


class DataMigrationDetectionTestCase(unittest.TestCase):
    def setUp(self, *args, **kwargs):
        self.test_project_path = os.path.dirname(settings.BASE_DIR)
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
        )

    def test_reverse_data_migration(self):
        self.assertEqual(0, self.linter.nb_warnings)
        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0002_missing_reverse")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertFalse(self.linter.has_errors)

    def test_reverse_data_migration_ignore(self):
        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertFalse(self.linter.has_errors)

    def test_exclude_warning_from_test(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            exclude_migration_tests=("RUNPYTHON_REVERSIBLE",),
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0002_missing_reverse")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_valid)
        self.assertFalse(self.linter.has_errors)

    def test_all_warnings_as_errors(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            all_warnings_as_errors=True,
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_erroneous)
        self.assertTrue(self.linter.has_errors)

    def test_warnings_as_errors_tests_matches(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            warnings_as_errors_tests=["RUNPYTHON_ARGS_NAMING_CONVENTION"],
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_erroneous)
        self.assertTrue(self.linter.has_errors)

    def test_warnings_as_errors_tests_no_match(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            warnings_as_errors_tests=[
                "RUNPYTHON_MODEL_IMPORT",
                "RUNPYTHON_MODEL_VARIABLE_NAME",
            ],
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertEqual(0, self.linter.nb_erroneous)
        self.assertFalse(self.linter.has_errors)

    def test_partial_function(self):
        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0004_partial_function")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(1, self.linter.nb_warnings)
        self.assertFalse(self.linter.has_errors)


class DataMigrationModelImportTestCase(unittest.TestCase):
    def test_missing_get_model_import(self):
        def incorrect_importing_model_forward(apps, schema_editor):
            from tests.test_project.app_data_migrations.models import MyModel

            MyModel.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(
            incorrect_importing_model_forward
        )
        self.assertEqual(1, len(issues))

    def test_correct_get_model_import(self):
        def correct_importing_model_forward(apps, schema_editor):
            MyModel = apps.get_model("app_data_migrations", "MyModel")
            MyVeryLongLongLongModel = apps.get_model(
                "app_data_migrations", "MyVeryLongLongLongModel"
            )
            MultiLineModel = apps.get_model(
                "app_data_migrations",
                "MultiLineModel",
            )

            MyModel.objects.filter(id=1).first()
            MyVeryLongLongLongModel.objects.filter(id=1).first()
            MultiLineModel.objects.all()

        issues = MigrationLinter.get_runpython_model_import_issues(
            correct_importing_model_forward
        )
        self.assertEqual(0, len(issues))

    def test_not_overlapping_model_name(self):
        """
        Correct for the import error, but should raise a warning.
        """

        def forward_method(apps, schema_editor):
            User = apps.get_model("auth", "CustomUserModel")

            User.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(0, len(issues))

    def test_correct_one_param_get_model_import(self):
        def forward_method(apps, schema_editor):
            User = apps.get_model("auth.User")

            User.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(0, len(issues))

    def test_not_overlapping_one_param(self):
        """
        Not an error, but should raise a warning.
        """

        def forward_method(apps, schema_editor):
            User = apps.get_model("auth.CustomUserModel")

            User.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(0, len(issues))

    def test_m2m_through_orm_usage(self):
        def forward_method(apps, schema_editor):
            MyModel = apps.get_model("myapp", "MyModel")

            MyModel.many_to_many.through.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(0, len(issues))

    def test_missing_m2m_through_orm(self):
        def forward_method(apps, schema_editor):
            from tests.test_project.app_data_migrations.models import MyModel

            MyModel.many_to_many.through.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(1, len(issues))


class DataMigrationModelVariableNamingTestCase(unittest.TestCase):
    def test_same_variable_name(self):
        def forward_op(apps, schema_editor):
            MyModel = apps.get_model("app", "MyModel")

            MyModel.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(0, len(issues))

    def test_same_variable_name_multiline(self):
        def forward_op(apps, schema_editor):
            MyModelVeryLongLongLongLongLong = apps.get_model(
                "app", "MyModelVeryLongLongLongLongLong"
            )

            MyModelVeryLongLongLongLongLong.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(0, len(issues))

    def test_same_variable_name_multiline2(self):
        def forward_op(apps, schema_editor):
            MyModelVeryLongLongLongLongLong = apps.get_model(
                "app_name_longlonglonglongapp",
                "MyModelVeryLongLongLongLongLong",
            )

            MyModelVeryLongLongLongLongLong.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(0, len(issues))

    def test_different_variable_name(self):
        def forward_op(apps, schema_editor):
            some_model = apps.get_model("app", "MyModel")

            some_model.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(1, len(issues))

    def test_diff_variable_name_multiline(self):
        def forward_op(apps, schema_editor):
            MyModelVeryLongLongLongLongLongNot = apps.get_model(
                "app", "MyModelVeryLongLongLongLongLong"
            )

            MyModelVeryLongLongLongLongLongNot.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(1, len(issues))

    def test_diff_variable_name_multiline2(self):
        def forward_op(apps, schema_editor):
            MyModelVeryLongLongLongLongLongNot = apps.get_model(
                "app_name_longlonglonglongapp",
                "MyModelVeryLongLongLongLongLong",
            )

            MyModelVeryLongLongLongLongLongNot.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(1, len(issues))

    def test_same_variable_name_one_param(self):
        def forward_op(apps, schema_editor):
            MyModel = apps.get_model("app.MyModel")

            MyModel.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(0, len(issues))

    def test_different_variable_name_one_param(self):
        def forward_op(apps, schema_editor):
            mymodel = apps.get_model("app.MyModel")

            mymodel.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(1, len(issues))

    def test_correct_variable_name_one_param_multiline(self):
        def forward_op(apps, schema_editor):
            AVeryLongModelName = apps.get_model(
                "quite_long_app_name.AVeryLongModelName"
            )

            AVeryLongModelName.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(0, len(issues))

    def test_different_variable_name_one_param_multiline(self):
        def forward_op(apps, schema_editor):
            m = apps.get_model(
                "quite_long_app_name_name_name.AVeryLongModelNameNameName"
            )

            m.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_variable_naming_issues(forward_op)
        self.assertEqual(1, len(issues))


class MixedRunPythonOperationsTestCase(unittest.TestCase):
    def setUp(self):
        test_project_path = os.path.dirname(settings.BASE_DIR)
        self.linter = MigrationLinter(
            test_project_path,
            include_apps=fixtures.MIXED_RUNPYTHON_OPERATIONS,
        )

    def test_mixed_runpython_with_schema_operations(self):
        """Test that mixing RunPython with schema operations produces an error."""
        mixed_migration = self.linter.migration_loader.disk_migrations[
            ("app_mixed_runpython_operations", "0002_mixed_operations")
        ]
        self.linter.lint_migration(mixed_migration)

        self.assertEqual(1, self.linter.nb_erroneous)
        self.assertTrue(self.linter.has_errors)
        self.assertEqual(0, self.linter.nb_valid)

    def test_runpython_only(self):
        """Test that RunPython-only migrations pass without errors."""
        runpython_only_migration = self.linter.migration_loader.disk_migrations[
            ("app_mixed_runpython_operations", "0003_runpython_only")
        ]
        self.linter.lint_migration(runpython_only_migration)

        self.assertEqual(0, self.linter.nb_erroneous)
        self.assertFalse(self.linter.has_errors)
        # Might have warnings for other checks (reversible, etc), but no errors
        self.assertTrue(self.linter.nb_valid >= 1 or self.linter.nb_warnings >= 1)

    def test_runpython_with_runsql(self):
        """Test that RunPython with RunSQL is allowed (both are data migrations)."""
        mixed_data_migration = self.linter.migration_loader.disk_migrations[
            ("app_mixed_runpython_operations", "0004_runpython_with_runsql")
        ]
        self.linter.lint_migration(mixed_data_migration)

        self.assertEqual(0, self.linter.nb_erroneous)
        self.assertFalse(self.linter.has_errors)

    def test_exclude_mixed_operations_check(self):
        """Test that RUNPYTHON_MIXED_OPERATIONS can be excluded."""
        self.linter = MigrationLinter(
            os.path.dirname(settings.BASE_DIR),
            include_apps=fixtures.MIXED_RUNPYTHON_OPERATIONS,
            exclude_migration_tests=("RUNPYTHON_MIXED_OPERATIONS",),
        )

        mixed_migration = self.linter.migration_loader.disk_migrations[
            ("app_mixed_runpython_operations", "0002_mixed_operations")
        ]
        self.linter.lint_migration(mixed_migration)

        # Should not error when excluded
        self.assertEqual(0, self.linter.nb_erroneous)
        self.assertFalse(self.linter.has_errors)
        # Should be valid since the check is excluded
        self.assertEqual(1, self.linter.nb_valid)


class RunSQLMigrationTestCase(unittest.TestCase):
    def setUp(self):
        test_project_path = os.path.dirname(settings.BASE_DIR)
        self.linter = MigrationLinter(
            test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
        )

    def test_missing_reserve_migration(self):
        runsql = migrations.RunSQL("sql;")

        error, ignored, warning = self.linter.lint_runsql(runsql)
        self.assertEqual("RUNSQL_REVERSIBLE", warning[0].code)

    def test_sql_linting_error(self):
        runsql = migrations.RunSQL("ALTER TABLE t DROP COLUMN t;")

        error, ignored, warning = self.linter.lint_runsql(runsql)
        self.assertEqual("DROP_COLUMN", error[0].code)

    def test_sql_linting_error_array(self):
        runsql = migrations.RunSQL(
            ["ALTER TABLE t DROP COLUMN c;", "ALTER TABLE t RENAME COLUMN c;"]
        )

        error, ignored, warning = self.linter.lint_runsql(runsql)
        self.assertEqual("DROP_COLUMN", error[0].code)
        self.assertEqual("RENAME_COLUMN", error[1].code)

    def test_sql_linting_error_args(self):
        runsql = migrations.RunSQL([("ALTER TABLE %s DROP COLUMN %s;", ("t", "c"))])

        error, ignored, warning = self.linter.lint_runsql(runsql)
        self.assertEqual("DROP_COLUMN", error[0].code)
