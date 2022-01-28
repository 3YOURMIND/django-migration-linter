import re

from .base import BaseAnalyser


class SqliteAnalyser(BaseAnalyser):
    migration_tests = [
        {
            "code": "RENAME_TABLE",
            "fn": lambda sql, **kw: re.search("ALTER TABLE .* RENAME TO", sql)
            and "__old" not in sql
            and "new__" not in sql,
            "type": "error",
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
            "type": "error",
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
            "type": "error",
        },
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
