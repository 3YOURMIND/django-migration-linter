import os

from django.conf import settings
from django.core.management.commands.makemigrations import (
    Command as MakeMigrationsCommand,
)
from django.db.migrations.writer import MigrationWriter

from django_migration_linter import MigrationLinter

from ..utils import register_linting_configuration_options


class Command(MakeMigrationsCommand):
    help = "Creates new migration(s) for apps and lints them."

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--lint", action="store_true", help="Lint newly generated migrations.",
        )
        register_linting_configuration_options(parser)

    def handle(self, *app_labels, **options):
        self.lint = options["lint"]
        self.database = options["database"]
        self.exclude_migrations_tests = options["exclude_migration_tests"]
        self.warnings_as_errors = options["warnings_as_errors"]
        return super(Command, self).handle(*app_labels, **options)

    def write_migration_files(self, changes):
        super(Command, self).write_migration_files(changes)
        if (
            not getattr(settings, "MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS", False)
            and not self.lint
        ):
            return

        # Lint migrations
        linter = MigrationLinter(
            path=os.environ["DJANGO_SETTINGS_MODULE"],
            database=self.database,
            no_cache=True,
            exclude_migration_tests=self.exclude_migrations_tests,
            warnings_as_errors=self.warnings_as_errors,
        )

        for app_label, app_migrations in changes.items():
            if self.verbosity >= 1:
                self.stdout.write(
                    self.style.MIGRATE_HEADING("Linting for '%s':" % app_label) + "\n"
                )
            for migration in app_migrations:
                linter.lint_migration(migration)
                if linter.has_errors:
                    writer = MigrationWriter(migration)
                    os.remove(writer.path)

                    if self.verbosity >= 1:
                        try:
                            migration_string = os.path.relpath(writer.path)
                        except ValueError:
                            migration_string = writer.path
                        if migration_string.startswith(".."):
                            migration_string = writer.path
                        self.stdout.write(
                            "Deleted %s\n"
                            % (self.style.MIGRATE_LABEL(migration_string))
                        )
                linter.reset_counters()
