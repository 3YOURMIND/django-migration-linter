from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterable, Type

if TYPE_CHECKING:
    from sql_analyser.base import Issue

from django_migration_linter.sql_analyser import (
    BaseAnalyser,
    MySqlAnalyser,
    PostgresqlAnalyser,
    SqliteAnalyser,
)

logger = logging.getLogger("django_migration_linter")

ANALYSER_STRING_MAPPING: dict[str, Type[BaseAnalyser]] = {
    "sqlite": SqliteAnalyser,
    "mysql": MySqlAnalyser,
    "postgresql": PostgresqlAnalyser,
}


def get_sql_analyser_class(
    database_vendor: str, analyser_string: str | None = None, **kwargs: Any
) -> Type[BaseAnalyser]:
    if analyser_string:
        return get_sql_analyser_from_string(analyser_string, **kwargs)
    return get_sql_analyser_class_from_db_vendor(database_vendor)


def get_sql_analyser_from_string(analyser_string: str, **kwargs) -> Type[BaseAnalyser]:
    final_mapping = ANALYSER_STRING_MAPPING.copy()
    final_mapping.update(kwargs.get("analyser_string_mapping", {}))
    if analyser_string not in final_mapping:
        raise ValueError(
            "Unknown SQL analyser '{}'. Known values: '{}'".format(
                analyser_string,
                "','".join(final_mapping.keys()),
            )
        )
    return final_mapping[analyser_string]


def get_sql_analyser_class_from_db_vendor(database_vendor: str) -> Type[BaseAnalyser]:
    sql_analyser_class: Type[BaseAnalyser]
    if "mysql" in database_vendor:
        sql_analyser_class = MySqlAnalyser
    elif "postgre" in database_vendor:
        sql_analyser_class = PostgresqlAnalyser
    elif "sqlite" in database_vendor:
        sql_analyser_class = SqliteAnalyser
    else:
        raise ValueError(
            "Unsupported database vendor '{}'. Try specifying an SQL analyser.".format(
                database_vendor
            )
        )

    logger.debug("Chosen SQL analyser class: %s", sql_analyser_class)
    return sql_analyser_class


def analyse_sql_statements(
    sql_analyser_class: Type[BaseAnalyser],
    sql_statements: list[str],
    exclude_migration_tests: Iterable[str] | None = None,
) -> tuple[list[Issue], list[Issue], list[Issue]]:
    sql_analyser = sql_analyser_class(exclude_migration_tests)
    sql_analyser.analyse(sql_statements)
    return sql_analyser.errors, sql_analyser.ignored, sql_analyser.warnings
