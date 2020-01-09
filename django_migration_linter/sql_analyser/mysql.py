import re

from .base import BaseAnalyser


class MySqlAnalyser(BaseAnalyser):
    migration_tests = [
        {
            "code": "ALTER_COLUMN",
            "fn": lambda sql, **kw: re.search(
                "ALTER TABLE .* MODIFY .* (?!NULL);?$", sql
            ),
            "mode": "one_liner",
        }
    ]

    @staticmethod
    def detect_column(sql):
        if isinstance(sql, str):
            regex_result = re.search("COLUMN [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)
            regex_result = re.search("MODIFY [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)
