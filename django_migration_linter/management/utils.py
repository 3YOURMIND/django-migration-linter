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
        action="store_true",
        help="handle warnings as errors",
    )
