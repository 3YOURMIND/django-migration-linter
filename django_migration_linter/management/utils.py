from __future__ import annotations

from typing import Any, Callable
import configparser
import logging
import itertools
import os

import toml

from django.core.management import CommandParser
from django.conf import settings

from ..sql_analyser.analyser import ANALYSER_STRING_MAPPING


CONFIG_NAME = "django_migration_linter"
PYPROJECT_TOML = "pyproject.toml"
DEFAULT_CONFIG_FILES = (
    f".{CONFIG_NAME}.cfg",
    "setup.cfg",
    "tox.ini",
)


def register_linting_configuration_options(parser: CommandParser) -> None:
    parser.add_argument(
        "--database",
        type=str,
        nargs="?",
        help=(
            "specify the database for which to generate the SQL. Defaults to default"
        ),
    )

    parser.add_argument(
        "--exclude-migration-tests",
        type=str,
        nargs="*",
        help="Specify backward incompatible migration tests "
        "to be ignored (e.g. ALTER_COLUMN)",
    )

    parser.add_argument(
        "--warnings-as-errors",
        type=str,
        nargs="*",
        help="handle warnings as errors. Optionally specify the tests to handle as "
        "errors (e.g. RUNPYTHON_REVERSIBLE)",
    )

    parser.add_argument(
        "--sql-analyser",
        nargs="?",
        choices=list(ANALYSER_STRING_MAPPING.keys()),
        help="select the SQL analyser",
    )


def configure_logging(verbosity: int) -> None:
    logger = logging.getLogger("django_migration_linter")

    if verbosity > 1:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    elif verbosity == 0:
        logger.disabled = True
    else:
        logging.basicConfig(format="%(message)s")


def extract_warnings_as_errors_option(
    warnings_as_errors: list[str] | None,
) -> tuple[list[str] | None, bool]:
    if isinstance(warnings_as_errors, list):
        warnings_as_errors_tests = warnings_as_errors
        # If the option is specified but without any test codes,
        # all warnings become errors
        all_warnings_as_errors = len(warnings_as_errors) == 0
    else:
        warnings_as_errors_tests = None
        all_warnings_as_errors = False

    return warnings_as_errors_tests, all_warnings_as_errors

def set_defaults_from_conf(parser) -> None:
    """
    Load options defined in config.

    Settings are loaded in priority order, where higher
    priority settings override lower.

    1. Django Settings
    2. Config files
    3. pyproject.toml

    Any command line options then override config file args.
    """

    # Parse args to get the relevant options for the current command
    args = parser.parse_args()
    options = vars(args)

    # Retrieve relevant config values
    toml_options = read_toml_file(options)
    config_options = read_config_file(options)
    django_settings_options = read_django_settings(options)

    # Merge values from configs in priority order toml -> conf -> settings
    conf_options = {k:v for k,v in itertools.chain(toml_options.items(),config_options.items(),django_settings_options.items())}

    # Override default argparse arguments with conf options
    parser.set_defaults(**conf_options)


def read_django_settings(options: dict[str, Any]) -> dict[str, Any]:
    """
    Read configuration from django settings
    """
    django_settings_options = dict()

    django_migration_linter_settings = getattr(
        settings, "MIGRATION_LINTER_OPTIONS", dict()
    )
    for key in options:
        if key in django_migration_linter_settings:
            django_settings_options[key] = django_migration_linter_settings[key]

    return django_migration_linter_settings


def read_config_file(options: dict[str, Any]) -> dict[str, Any]:
    """
    Read config options from any of the supported files specified
    in DEFAULT_CONFIG_FILES.
    """
    config_options = dict()

    config_parser = configparser.ConfigParser()
    config_parser.read(DEFAULT_CONFIG_FILES, encoding="utf-8")
    for key, value in options.items():
        config_get_fn: Callable
        if isinstance(value, bool):
            config_get_fn = config_parser.getboolean
        else:
            config_get_fn = config_parser.get

        config_value = config_get_fn(CONFIG_NAME, key, fallback=None)
        if config_value is not None:
            config_options[key] = config_value
    return config_options


def read_toml_file(options: dict[str, Any]) -> dict[str, Any]:
    """
    Read config options from toml file.
    """
    toml_options = dict()

    if os.path.exists(PYPROJECT_TOML):
        pyproject_toml = toml.load(PYPROJECT_TOML)
        section = pyproject_toml.get("tool", {}).get(CONFIG_NAME, {})
        for key in options:
            if key in section:
                toml_options[key] = section[key]

    return toml_options