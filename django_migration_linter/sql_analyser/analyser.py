import logging

from django_migration_linter.sql_analyser import (
    BaseAnalyser,
    MySqlAnalyser,
    PostgresqlAnalyser,
    SqliteAnalyser,
)

logger = logging.getLogger(__name__)


def get_sql_analyser(database_vendor, exclude_migration_tests=None):
    if "mysql" in database_vendor:
        sql_analyser_class = MySqlAnalyser
    elif "postgre" in database_vendor:
        sql_analyser_class = PostgresqlAnalyser
    elif "sqlite" in database_vendor:
        sql_analyser_class = SqliteAnalyser
    else:
        sql_analyser_class = BaseAnalyser

    logger.debug("Chosen SQL analyser class: %s", sql_analyser_class)
    return sql_analyser_class(exclude_migration_tests)


def analyse_sql_statements(
    sql_statements, database_vendor, exclude_migration_tests=None
):
    sql_analyser = get_sql_analyser(database_vendor, exclude_migration_tests)
    sql_analyser.analyse(sql_statements)
    return sql_analyser.errors, sql_analyser.ignored
