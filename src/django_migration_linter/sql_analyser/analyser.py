from __future__ import annotations

import importlib
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


def _load_custom_mapping(
    custom_mapping: dict[str, str | Type[BaseAnalyser]],
) -> dict[str, Type[BaseAnalyser]]:
    """
    Load custom mapping for SQL analysers.
    """
    result = {}
    for key, val in custom_mapping.items():
        if isinstance(val, str):
            try:
                module_name, class_name = val.rsplit(".", 1)
                module = importlib.import_module(module_name)
                analyser_class = getattr(module, class_name)
                result[key] = analyser_class
            except Exception as x:
                raise ValueError(
                    f"Custom mapping value for '{key}' must be a fully qualified "
                    f"SQL analyser class name: '{val}'",
                ) from x
        elif issubclass(val, BaseAnalyser):
            result[key] = val
        else:
            raise ValueError(
                f"Custom mapping value for '{key}' must be a fully qualified "
                f"SQL analyser class name or a subclass of BaseAnalyser: '{val}'",
            )
    return result


def get_sql_analyser_class(
    database_vendor: str, analyser_string: str | None = None, **kwargs: Any
) -> Type[BaseAnalyser]:
    if analyser_string:
        return get_sql_analyser_from_string(analyser_string, **kwargs)
    return get_sql_analyser_class_from_db_vendor(database_vendor)


def get_sql_analyser_from_string(analyser_string: str, **kwargs) -> Type[BaseAnalyser]:
    final_mapping = ANALYSER_STRING_MAPPING.copy()
    custom_mapping = kwargs.get("analyser_string_mapping", {})
    if custom_mapping:
        custom_mapping = _load_custom_mapping(custom_mapping)
        final_mapping.update(custom_mapping)
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
