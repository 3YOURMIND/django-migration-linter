import logging

from django_migration_linter.sql_analyser import (
    MySqlAnalyser,
    PostgresqlAnalyser,
    SqliteAnalyser,
)

logger = logging.getLogger("django_migration_linter")

ANALYSER_STRING_MAPPING = {
    "sqlite": SqliteAnalyser,
    "mysql": MySqlAnalyser,
    "postgresql": PostgresqlAnalyser,
}


def get_sql_analyser_class(database_vendor, analyser_string=None):
    if analyser_string:
        return get_sql_analyser_from_string(analyser_string)
    return get_sql_analyser_class_from_db_vendor(database_vendor)


def get_sql_analyser_from_string(analyser_string):
    if analyser_string not in ANALYSER_STRING_MAPPING:
        raise ValueError(
            "Unknown SQL analyser. Known values: {}".format(analyser_string.keys())
        )
    return ANALYSER_STRING_MAPPING[analyser_string]


def get_sql_analyser_class_from_db_vendor(database_vendor):
    if "mysql" in database_vendor:
        sql_analyser_class = MySqlAnalyser
    elif "postgre" in database_vendor:
        sql_analyser_class = PostgresqlAnalyser
    elif "sqlite" in database_vendor:
        sql_analyser_class = SqliteAnalyser
    else:
        raise ValueError("Unsupported database vendor. Try specifying an SQL analyser.")

    logger.debug("Chosen SQL analyser class: %s", sql_analyser_class)
    return sql_analyser_class


def analyse_sql_statements(
    sql_analyser_class, sql_statements, exclude_migration_tests=None
):
    sql_analyser = sql_analyser_class(exclude_migration_tests)
    sql_analyser.analyse(sql_statements)
    return sql_analyser.errors, sql_analyser.ignored, sql_analyser.warnings
