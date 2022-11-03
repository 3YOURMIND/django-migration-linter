import re

from .base import BaseAnalyser


def has_create_index(sql_statements, **kwargs):
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
    migration_tests = [
        {
            "code": "CREATE_INDEX",
            "fn": has_create_index,
            "msg": "CREATE INDEX locks table",
            "mode": "transaction",
            "type": "warning",
        },
        {
            "code": "DROP_INDEX",
            "fn": lambda sql, **kw: re.search("DROP INDEX", sql)
            and not re.search("INDEX CONCURRENTLY", sql),
            "msg": "DROP INDEX locks table",
            "mode": "one_liner",
            "type": "warning",
        },
        {
            "code": "REINDEX",
            "fn": lambda sql, **kw: sql.startswith("REINDEX"),
            "msg": "REINDEX locks table",
            "mode": "one_liner",
            "type": "warning",
        },
    ]
