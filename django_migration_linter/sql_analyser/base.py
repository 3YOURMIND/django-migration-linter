# Copyright 2019 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import re

from .utils import update_migration_tests, build_error_dict

logger = logging.getLogger(__name__)


def has_not_null_column(sql_statements, **kwargs):
    # TODO: improve to detect that the same column is concerned
    return any(
        re.search("(?<!DROP )NOT NULL", sql) and not sql.startswith("CREATE TABLE")
        for sql in sql_statements
    ) and not any("SET DEFAULT" in sql for sql in sql_statements)


class BaseAnalyser(object):
    base_migration_tests = [
        {
            "code": "RENAME_TABLE",
            "fn": lambda sql, **kw: re.search("RENAME TABLE", sql)
            or re.search("ALTER TABLE .* RENAME TO", sql),
            "err_msg": "RENAMING tables",
            "mode": "one_liner",
        },
        {
            "code": "NOT_NULL",
            "fn": has_not_null_column,
            "err_msg": "NOT NULL constraint on columns",
            "mode": "transaction",
        },
        {
            "code": "DROP_COLUMN",
            "fn": lambda sql, **kw: re.search("DROP COLUMN", sql),
            "err_msg": "DROPPING columns",
            "mode": "one_liner",
        },
        {
            "code": "DROP_TABLE",
            "fn": lambda sql, **kw: sql.startswith("DROP TABLE"),
            "err_msg": "DROPPING table",
            "mode": "one_liner",
        },
        {
            "code": "RENAME_COLUMN",
            "fn": lambda sql, **kw: re.search("ALTER TABLE .* CHANGE", sql)
            or re.search("ALTER TABLE .* RENAME COLUMN", sql),
            "err_msg": "RENAMING columns",
            "mode": "one_liner",
        },
        {
            "code": "ALTER_COLUMN",
            "fn": lambda sql, **kw: re.search(
                "ALTER TABLE .* ALTER COLUMN .* TYPE", sql
            ),
            "err_msg": (
                "ALTERING columns (Could be backward compatible. "
                "You may ignore this migration.)"
            ),
            "mode": "one_liner",
        },
        {
            "code": "ADD_UNIQUE",
            "fn": lambda sql, **kw: re.search(
                "ALTER TABLE .* ADD CONSTRAINT .* UNIQUE", sql
            ),
            "err_msg": "ADDING unique constraint",
            "mode": "one_liner",
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
            if test["code"] in self.exclude_migration_tests:
                logger.debug("Testing %s -- IGNORED", sql)
                err = build_error_dict(migration_test=test, sql_statement=sql)
                self.ignored.append(err)
            else:
                logger.debug("Testing %s -- ERROR", sql)
                err = build_error_dict(migration_test=test, sql_statement=sql)
                self.errors.append(err)
        else:
            logger.debug("Testing %s -- PASSED", sql)
