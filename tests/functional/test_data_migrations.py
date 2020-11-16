import os
import unittest

from django.conf import settings

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
            exclude_migration_tests=("REVERSIBLE_DATA_MIGRATION",),
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0002_missing_reverse")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_valid)
        self.assertFalse(self.linter.has_errors)

    def test_warnings_as_errors(self):
        self.linter = MigrationLinter(
            self.test_project_path,
            include_apps=fixtures.DATA_MIGRATIONS,
            warnings_as_errors=True,
        )

        reverse_migration = self.linter.migration_loader.disk_migrations[
            ("app_data_migrations", "0003_incorrect_arguments")
        ]
        self.linter.lint_migration(reverse_migration)

        self.assertEqual(0, self.linter.nb_warnings)
        self.assertEqual(1, self.linter.nb_erroneous)
        self.assertTrue(self.linter.has_errors)


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
        Correct for the import error, but should raise a warning
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
        Not an error, but should raise a warning
        """

        def forward_method(apps, schema_editor):
            User = apps.get_model("auth.CustomUserModel")

            User.objects.filter(id=1).first()

        issues = MigrationLinter.get_runpython_model_import_issues(forward_method)
        self.assertEqual(0, len(issues))


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
