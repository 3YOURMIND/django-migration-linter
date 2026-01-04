from __future__ import annotations

import argparse
import logging

from django.core.management import CommandParser

from ..sql_analyser.analyser import ANALYSER_STRING_MAPPING


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
        "--all-warnings-as-errors",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="treat all warnings as errors",
    )
    parser.add_argument(
        "--warning-as-error",
        type=str,
        nargs="*",
        help="treat specified tests as errors. Specify the tests through their code "
        "(e.g. RUNPYTHON_REVERSIBLE)",
    )

    parser.add_argument(
        "--sql-analyser",
        nargs="?",
        choices=list(ANALYSER_STRING_MAPPING.keys()),
        help="select the SQL analyser",
    )

    parser.add_argument(
        "--ignore-sqlmigrate-errors",
        action="store_true",
        help="ignore failures of sqlmigrate command",
    )

    parser.add_argument(
        "--ignore-initial-migrations",
        action="store_true",
        help="ignore initial migrations",
    )


def configure_logging(verbosity: int) -> None:
    logger = logging.getLogger("django_migration_linter")

    if verbosity > 1:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    elif verbosity == 0:
        logger.disabled = True
    else:
        logging.basicConfig(format="%(message)s")
