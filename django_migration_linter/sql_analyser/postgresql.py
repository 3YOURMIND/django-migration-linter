from __future__ import annotations

import re

from .base import BaseAnalyser, Check, CheckMode, CheckType


def has_create_index(sql_statements: list[str], **kwargs) -> bool:
    regex_result = None
    for sql in sql_statements:
        regex_result = re.search(r"CREATE (UNIQUE )?INDEX.*ON (.*) \(", sql)
        if re.search("INDEX CONCURRENTLY", sql):
            regex_result = None
        elif regex_result:
            break
    if not regex_result:
        return False

    concerned_table = regex_result.group(2)
    table_is_added_in_transaction = any(
        sql.startswith(f"CREATE TABLE {concerned_table}") for sql in sql_statements
    )
    return not table_is_added_in_transaction


class PostgresqlAnalyser(BaseAnalyser):
    migration_checks: list[Check] = [
        Check(
            code="CREATE_INDEX",
            fn=has_create_index,
            message="CREATE INDEX locks table",
            mode=CheckMode.TRANSACTION,
            type=CheckType.WARNING,
        ),
        Check(
            code="DROP_INDEX",
            fn=lambda sql, **kw: re.search("DROP INDEX", sql)
            and not re.search("INDEX CONCURRENTLY", sql),
            message="DROP INDEX locks table",
            mode=CheckMode.ONE_LINER,
            type=CheckType.WARNING,
        ),
        Check(
            code="REINDEX",
            fn=lambda sql, **kw: sql.startswith("REINDEX"),
            message="REINDEX locks table",
            mode=CheckMode.ONE_LINER,
            type=CheckType.WARNING,
        ),
    ]
