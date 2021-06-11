import re

from .base import BaseAnalyser


class PostgresqlAnalyser(BaseAnalyser):
    migration_tests = [
        {
            "code": "CREATE_INDEX",
            "fn": lambda sql, **kw: re.search("CREATE (UNIQUE )?INDEX", sql)
            and not re.search("INDEX CONCURRENTLY", sql),
            "msg": "CREATE INDEX locks table",
            "mode": "one_liner",
            "type": "warning",
        },
        {
            "code": "DROP_INDEX",
            "fn": lambda sql, **kw: re.search("DROP INDEX", sql) and not re.search("INDEX CONCURRENTLY", sql),
            "msg": "DROP INDEX locks table",
            "mode": "one_liner",
            "type": "warning",
        },
    ]
