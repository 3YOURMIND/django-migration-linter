from django.core.management.commands.makemigrations import (
    Command as MakeMigrationsCommand,
)
from django.db.migrations import Migration

from django_migration_linter import MigrationLinter


class Command(MakeMigrationsCommand):
    help = "Creates new migration(s) for apps and applies the migration linter."

    def handle(self, *app_labels, **options):
        if settings.MIGRATION_LINTER_MAKE_MIGRATIONS or linted_migrations_options:
            my_logic()
        else:
            return super(Command, self).handle(*app_labels, **options)

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        # TODO: add options to select/unselect migration rules

    def write_migration_files(self, changes):
        super(Command, self).write_migration_files(changes)

        if options["project_root_path"]:
            settings_path = options["project_root_path"]
        else:
            settings_path = os.path.dirname(
                import_module(os.getenv("DJANGO_SETTINGS_MODULE")).__file__
            )
        linter = MigrationLinter(settings_path)

        self.stdout.write(self.style.MIGRATE_XXX("Linting merging"))
        # Iterate over changes to apply the linter
        for app_label, app_migrations in changes.values():
            for migration in app_migrations:
                error = linter.lint_migration(migration)

                if not self.dry_run:
                    pass # delete
