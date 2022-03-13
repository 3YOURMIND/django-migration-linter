import logging


def register_linting_configuration_options(parser):
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


def configure_logging(verbosity):
    logger = logging.getLogger("django_migration_linter")

    if verbosity > 1:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    elif verbosity == 0:
        logger.disabled = True
    else:
        logging.basicConfig(format="%(message)s")


def extract_warnings_as_errors_option(warnings_as_errors):
    if isinstance(warnings_as_errors, list):
        warnings_as_errors_tests = warnings_as_errors
        # If the option is specified but without any test codes,
        # all warnings become errors
        all_warnings_as_errors = len(warnings_as_errors) == 0
    else:
        warnings_as_errors_tests = None
        all_warnings_as_errors = False

    return warnings_as_errors_tests, all_warnings_as_errors
