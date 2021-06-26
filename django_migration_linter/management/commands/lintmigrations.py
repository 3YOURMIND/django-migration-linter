import configparser
import logging
import os
import sys
from importlib import import_module

import toml
from django.core.management.base import BaseCommand

from ...constants import __version__
from ...migration_linter import MessageType, MigrationLinter
from ..utils import register_linting_configuration_options

CONFIG_NAME = "django_migration_linter"
PYPROJECT_TOML = "pyproject.toml"
DEFAULT_CONFIG_FILES = (
    ".{}.cfg".format(CONFIG_NAME),
    "setup.cfg",
    "tox.ini",
)

logger = logging.getLogger("django_migration_linter")


class Command(BaseCommand):
    help = "Lint your migrations"

    def add_arguments(self, parser):
        parser.add_argument(
            "app_label",
            nargs="?",
            type=str,
            help="App label of an application to lint migrations.",
        )
        parser.add_argument(
            "migration_name",
            nargs="?",
            type=str,
            help="Linting will only be done on that migration only.",
        )
        parser.add_argument(
            "--git-commit-id",
            type=str,
            nargs="?",
            help=(
                "if specified, only migrations since this commit "
                "will be taken into account"
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
        elif options["verbosity"] == 0:
            logger.disabled = True
        else:
            logging.basicConfig(format="%(message)s")

        keys = (
            "ignore_name_contains",
            "ignore_name",
            "include_name_contains",
            "include_name",
            "include_apps",
            "exclude_apps",
            "database",
            "cache_path",
            "no_cache",
            "applied_migrations",
            "unapplied_migrations",
            "exclude_migration_tests",
            "quiet",
            "warnings_as_errors",
        )
        boolean_keys = (
            "no_cache",
            "applied_migrations",
            "unapplied_migrations",
            "warnings_as_errors",
        )

        config = {key: options[key] for key in keys}

        config_parser = configparser.ConfigParser()
        config_parser.read(DEFAULT_CONFIG_FILES, encoding="utf-8")
        for key in keys:
            if key in boolean_keys:
                config_get_fn = config_parser.getboolean
            else:
                config_get_fn = config_parser.get

            config_value = config_get_fn(CONFIG_NAME, key, fallback=None)
            if config_value and not config[key]:
                config[key] = config_value

        if os.path.exists(PYPROJECT_TOML):
            pyproject_toml = toml.load(PYPROJECT_TOML)
            section = pyproject_toml.get("tool", {}).get(CONFIG_NAME, {})
            for key in keys:
                if key in section and not config[key]:
                    config[key] = section[key]

        linter = MigrationLinter(
            settings_path,
            ignore_name_contains=config["ignore_name_contains"],
            ignore_name=config["ignore_name"],
            include_name_contains=config["include_name_contains"],
            include_name=config["include_name"],
            include_apps=config["include_apps"],
            exclude_apps=config["exclude_apps"],
            database=config["database"],
            cache_path=config["cache_path"],
            no_cache=config["no_cache"],
            only_applied_migrations=config["applied_migrations"],
            only_unapplied_migrations=config["unapplied_migrations"],
            exclude_migration_tests=config["exclude_migration_tests"],
            quiet=config["quiet"],
            warnings_as_errors=config["warnings_as_errors"],
            no_output=options["verbosity"] == 0,
        )
        linter.lint_all_migrations(
            app_label=options["app_label"],
            migration_name=options["migration_name"],
            git_commit_id=options["git_commit_id"],
            migrations_file_path=options["include_migrations_from"],
        )
        linter.print_summary()
        if linter.has_errors:
            sys.exit(1)

    def get_version(self):
        return __version__
