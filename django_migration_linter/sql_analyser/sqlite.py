import re

from .base import BaseAnalyser


def has_add_unique(sql_statements, **kwargs):
    regex_result = None
    for sql in sql_statements:
        regex_result = re.search('CREATE UNIQUE INDEX .* ON (".*?")', sql)
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


class SqliteAnalyser(BaseAnalyser):
    migration_tests = [
        {
            "code": "RENAME_TABLE",
            "fn": lambda sql, **kw: re.search("ALTER TABLE .* RENAME TO", sql)
            and "__old" not in sql
            and "new__" not in sql,
        },
        {
            "code": "DROP_TABLE",
            # TODO: improve to detect that the table names overlap
            "fn": lambda sql_statements, **kw: any(
                sql.startswith("DROP TABLE") for sql in sql_statements
            )
            and not any(sql.startswith("CREATE TABLE") for sql in sql_statements),
            "msg": "DROPPING table",
            "mode": "transaction",
        },
        {
            "code": "NOT_NULL",
            "fn": lambda sql_statements, **kw: any(
                re.search("NOT NULL(?! PRIMARY)(?! DEFAULT)", sql)
                for sql in sql_statements
            )
            and any(
                re.search("ALTER TABLE .* RENAME TO", sql)
                and ("__old" in sql or "new__" in sql)
                for sql in sql_statements
            ),
            "mode": "transaction",
        },
        {"code": "ADD_UNIQUE", "fn": has_add_unique, "mode": "transaction"},
    ]

    @staticmethod
    def detect_table(sql):
        if isinstance(sql, str):
            regex_result = re.search("TABLE [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)
            regex_result = re.search("ON [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)
