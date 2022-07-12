from unittest.mock import patch

from django.core.management import call_command
from django.test import TransactionTestCase
from django.test.utils import override_settings


class LintMigrationsCommandTestCase(TransactionTestCase):
    databases = {"default", "sqlite"}

    def setUp(self):
        call_command("migrate", "app_unique_together", "0002")
        self.addCleanup(call_command, "migrate", "app_unique_together")
        super().setUp()

    def test_plain(self):
        with self.assertRaises(SystemExit):
            call_command("lintmigrations")

    def test_config_file_app_label(self):
        with patch(
            "django_migration_linter.management.commands.lintmigrations.Command.read_config_file"
        ) as config_fn:
            config_fn.return_value = {"app_label": "app_correct"}
            call_command("lintmigrations")

    def test_command_line_app_label(self):
        call_command("lintmigrations", app_label="app_correct")

    def test_command_line_and_config_file_app_label(self):
        with patch(
            "django_migration_linter.management.commands.lintmigrations.Command.read_config_file"
        ) as config_fn:
            config_fn.return_value = {"app_label": "app_correct"}

            with self.assertRaises(SystemExit):
                call_command("lintmigrations", app_label="app_drop_table")

    @override_settings(MIGRATION_LINTER_OPTIONS={"app_label": "app_correct"})
    def test_django_settings_option(self):
        call_command("lintmigrations")
