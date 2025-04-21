import re

from .base import BaseAnalyser


def has_create_index(sql_statements, **kwargs):
    regex_result = None
    for sql in sql_statements:
        regex_result = re.search(r"CREATE (UNIQUE )?INDEX.*ON (.*) \(", sql)
        if re.search(r"INDEX CONCURRENTLY", sql):
            regex_result = None
        elif regex_result:
            break
    if not regex_result:
        return False

    concerned_table = regex_result.group(2)
    table_is_added_in_transaction = any(
        sql.startswith("CREATE TABLE {}".format(concerned_table))
        for sql in sql_statements
    )
    return not table_is_added_in_transaction


def has_add_unique_column(sql_statements, **kwargs):
    regex_result = None
    for sql in sql_statements:
        regex_result = re.search(
            r"ALTER TABLE (.*) ADD COLUMN .*UNIQUE CONSTRAINT.*",
            sql
        )
        if regex_result:
            break
    if not regex_result:
        return False

    concerned_table = regex_result.group(1)
    table_is_added_in_transaction = any(
        sql.startswith("CREATE TABLE {}".format(concerned_table))
        for sql in sql_statements
    )
    return not table_is_added_in_transaction


def multiple_table_locks(sql_statements, **kwargs):
    """Returns true if there are more than 2 table locks

    go/created-at-migration-postportem
    """
    tables = set()

    for sql in sql_statements:
        result = re.search(r'ALTER TABLE "([\w]+)".*', sql)

        if result:
            table_name = result.group(1)
            tables.add(table_name)

    return len(tables) > 2


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
            "fn": lambda sql, **kw: re.search(r"DROP INDEX", sql)
            and not re.search(r"INDEX CONCURRENTLY", sql),
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
        {
            "code": "ADD_UNIQUE_COLUMN",
            "fn": has_add_unique_column,
            "msg": "Adding a column with UNIQUE CONSTRAINT locks table",
            "mode": "transaction",
            "type": "error",
        },
        {
            "code": "MULTIPLE_TABLE_LOCKS",
            "fn": multiple_table_locks,
            "msg": (
                "Do not lock more than two tables at a time in the same "
                "transaction to minimize the chance of deadlocks and "
                "production issues. go/created-at-migration-postportem"
            ),
            "mode": "transaction",
            "type": "error",
        }
    ]
