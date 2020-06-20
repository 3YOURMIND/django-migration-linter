import logging
import re

from .utils import update_migration_tests

logger = logging.getLogger(__name__)


def has_not_null_column(sql_statements, **kwargs):
    # TODO: improve to detect that the same column is concerned
    ends_with_default = None
    for sql in sql_statements:
        if "SET DEFAULT" in sql:
            ends_with_default = True
        elif "DROP DEFAULT" in sql:
            ends_with_default = False
    return (
        any(
            re.search("(?<!DROP )NOT NULL", sql) and not sql.startswith("CREATE TABLE")
            for sql in sql_statements
        )
        and ends_with_default is False
    )


def has_add_unique(sql_statements, **kwargs):
    regex_result = None
    for sql in sql_statements:
        regex_result = re.search("ALTER TABLE (.*) ADD CONSTRAINT .* UNIQUE", sql)
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


class BaseAnalyser(object):
    base_migration_tests = [
        {
            "code": "RENAME_TABLE",
            "fn": lambda sql, **kw: re.search("RENAME TABLE", sql)
            or re.search("ALTER TABLE .* RENAME TO", sql),
            "msg": "RENAMING tables",
            "mode": "one_liner",
        },
        {
            "code": "NOT_NULL",
            "fn": has_not_null_column,
            "msg": "NOT NULL constraint on columns",
            "mode": "transaction",
        },
        {
            "code": "DROP_COLUMN",
            "fn": lambda sql, **kw: re.search("DROP COLUMN", sql),
            "msg": "DROPPING columns",
            "mode": "one_liner",
        },
        {
            "code": "DROP_TABLE",
            "fn": lambda sql, **kw: sql.startswith("DROP TABLE"),
            "msg": "DROPPING table",
            "mode": "one_liner",
        },
        {
            "code": "RENAME_COLUMN",
            "fn": lambda sql, **kw: re.search("ALTER TABLE .* CHANGE", sql)
            or re.search("ALTER TABLE .* RENAME COLUMN", sql),
            "msg": "RENAMING columns",
            "mode": "one_liner",
        },
        {
            "code": "ALTER_COLUMN",
            "fn": lambda sql, **kw: re.search(
                "ALTER TABLE .* ALTER COLUMN .* TYPE", sql
            ),
            "msg": (
                "ALTERING columns (Could be backward compatible. "
                "You may ignore this migration.)"
            ),
            "mode": "one_liner",
        },
        {
            "code": "ADD_UNIQUE",
            "fn": has_add_unique,
            "msg": "ADDING unique constraint",
            "mode": "transaction",
        },
    ]

    migration_tests = []

    def __init__(self, exclude_migration_tests):
        self.exclude_migration_tests = exclude_migration_tests or []
        self.errors = []
        self.ignored = []
        self.migration_tests = update_migration_tests(
            self.base_migration_tests, self.migration_tests
        )

    def analyse(self, sql_statements):
        for statement in sql_statements:
            for test in self.one_line_migration_tests:
                self._test_sql(test, sql=statement)

        for test in self.transaction_migration_tests:
            self._test_sql(test, sql=sql_statements)

    @property
    def one_line_migration_tests(self):
        return [test for test in self.migration_tests if test["mode"] == "one_liner"]

    @property
    def transaction_migration_tests(self):
        return [test for test in self.migration_tests if test["mode"] == "transaction"]

    def _test_sql(self, test, sql):
        if test["fn"](sql, errors=self.errors):
            err = self.build_error_dict(migration_test=test, sql_statement=sql)
            if test["code"] in self.exclude_migration_tests:
                logger.debug("Testing %s -- IGNORED", sql)
                self.ignored.append(err)
            else:
                logger.debug("Testing %s -- ERROR", sql)
                self.errors.append(err)
        else:
            logger.debug("Testing %s -- PASSED", sql)

    def build_error_dict(self, migration_test, sql_statement):
        table = self.detect_table(sql_statement)
        col = self.detect_column(sql_statement)
        return {
            "msg": migration_test["msg"],
            "code": migration_test["code"],
            "table": table,
            "column": col,
        }

    @staticmethod
    def detect_table(sql):
        if isinstance(sql, str):
            regex_result = re.search("TABLE [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)

    @staticmethod
    def detect_column(sql):
        if isinstance(sql, str):
            regex_result = re.search("COLUMN [`\"'](.*?)[`\"']", sql, re.IGNORECASE)
            if regex_result:
                return regex_result.group(1)
