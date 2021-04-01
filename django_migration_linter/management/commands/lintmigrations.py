import configparser
import logging
import os
import sys
from importlib import import_module

from django.core.management.base import BaseCommand

from ...constants import __version__
from ...migration_linter import MessageType, MigrationLinter
from ..utils import register_linting_configuration_options

CONFIG_NAME = "django_migration_linter"
DEFAULT_CONFIG_FILES = (
    ".{}.cfg".format(CONFIG_NAME),
    "setup.cfg",
    "tox.ini",
)


class Command(BaseCommand):
    help = "Lint your migrations"

    def add_arguments(self, parser):
        parser.add_argument(
            "commit_id",
            metavar="GIT_COMMIT_ID",
            type=str,
            nargs="?",
            help=(
                "if specified, only migrations since this commit "
                "will be taken into account. If not specified, "
                "the initial repo commit will be used"
            ),
        )
        parser.add_argument(
            "--ignore-name-contains",
            type=str,
            nargs="?",
            help="ignore migrations containing this name",
        )
        parser.add_argument(
            "--ignore-name",
            type=str,
            nargs="*",
            help="ignore migrations with exactly one of these names",
        )
        parser.add_argument(
            "--include-name-contains",
            type=str,
            nargs="?",
            help="only consider migrations containing this name",
        )
        parser.add_argument(
            "--include-name",
            type=str,
            nargs="*",
            help="only consider migrations with exactly one of these names",
        )
        parser.add_argument(
            "--project-root-path", type=str, nargs="?", help="django project root path"
        )
        parser.add_argument(
            "--include-migrations-from",
            metavar="FILE_PATH",
            type=str,
            nargs="?",
            help="if specified, only migrations listed in the file will be considered",
        )
        cache_group = parser.add_mutually_exclusive_group(required=False)
        cache_group.add_argument(
            "--cache-path",
            type=str,
            help="specify a directory that should be used to store cache-files in.",
        )
        cache_group.add_argument(
            "--no-cache", action="store_true", help="don't use a cache"
        )

        incl_excl_group = parser.add_mutually_exclusive_group(required=False)
        incl_excl_group.add_argument(
            "--include-apps",
            type=str,
            nargs="*",
            help="check only migrations that are in the specified django apps",
        )
        incl_excl_group.add_argument(
            "--exclude-apps",
            type=str,
            nargs="*",
            help="ignore migrations that are in the specified django apps",
        )

        applied_unapplied_migrations_group = parser.add_mutually_exclusive_group(
            required=False
        )
        applied_unapplied_migrations_group.add_argument(
            "--unapplied-migrations",
            action="store_true",
            help="check only migrations have not been applied to the database yet",
        )
        applied_unapplied_migrations_group.add_argument(
            "--applied-migrations",
            action="store_true",
            help="check only migrations that have already been applied to the database",
        )

        parser.add_argument(
            "-q",
            "--quiet",
            nargs="+",
            choices=MessageType.values(),
            help="don't print linting messages to stdout",
        )
        register_linting_configuration_options(parser)

    def handle(self, *args, **options):
        if options["project_root_path"]:
            settings_path = options["project_root_path"]
        else:
            settings_path = os.path.dirname(
                import_module(os.getenv("DJANGO_SETTINGS_MODULE")).__file__
            )

        if options["verbosity"] > 1:
            logging.basicConfig(format="%(message)s", level=logging.DEBUG)
        else:
            logging.basicConfig(format="%(message)s")

        config_parser = configparser.ConfigParser()
        config_parser.read(DEFAULT_CONFIG_FILES, encoding="utf-8")

        ignore_name_contains = options["ignore_name_contains"] or config_parser.get(
            CONFIG_NAME, "ignore_name_contains", fallback=None
        )
        ignore_name = options["ignore_name"] or config_parser.get(
            CONFIG_NAME, "ignore_name", fallback=None
        )
        include_name_contains = options["include_name_contains"] or config_parser.get(
            CONFIG_NAME, "include_name_contains", fallback=None
        )
        include_name = options["include_name"] or config_parser.get(
            CONFIG_NAME, "include_name", fallback=None
        )
        include_apps = options["include_apps"] or config_parser.get(
            CONFIG_NAME, "include_apps", fallback=None
        )
        exclude_apps = options["exclude_apps"] or config_parser.get(
            CONFIG_NAME, "exclude_apps", fallback=None
        )
        database = options["database"] or config_parser.get(
            CONFIG_NAME, "database", fallback=None
        )
        cache_path = options["cache_path"] or config_parser.get(
            CONFIG_NAME, "cache_path", fallback=None
        )
        no_cache = options["no_cache"] or config_parser.getboolean(
            CONFIG_NAME, "no_cache", fallback=None
        )
        applied_migrations = options["applied_migrations"] or config_parser.getboolean(
            CONFIG_NAME, "applied_migrations", fallback=None
        )
        unapplied_migrations = options[
            "unapplied_migrations"
        ] or config_parser.getboolean(
            CONFIG_NAME, "unapplied_migrations", fallback=None
        )
        exclude_migration_tests = options[
            "exclude_migration_tests"
        ] or config_parser.get(CONFIG_NAME, "exclude_migration_tests", fallback=None)
        quiet = options["quiet"] or config_parser.get(
            CONFIG_NAME, "quiet", fallback=None
        )
        warnings_as_errors = options["warnings_as_errors"] or config_parser.getboolean(
            CONFIG_NAME, "warnings_as_errors", fallback=None
        )

        linter = MigrationLinter(
            settings_path,
            ignore_name_contains=ignore_name_contains,
            ignore_name=ignore_name,
            include_name_contains=include_name_contains,
            include_name=include_name,
            include_apps=include_apps,
            exclude_apps=exclude_apps,
            database=database,
            cache_path=cache_path,
            no_cache=no_cache,
            only_applied_migrations=applied_migrations,
            only_unapplied_migrations=unapplied_migrations,
            exclude_migration_tests=exclude_migration_tests,
            quiet=quiet,
            warnings_as_errors=warnings_as_errors,
        )
        linter.lint_all_migrations(
            git_commit_id=options["commit_id"],
            migrations_file_path=options["include_migrations_from"],
        )
        linter.print_summary()
        if linter.has_errors:
            sys.exit(1)

    def get_version(self):
        return __version__
