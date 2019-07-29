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

import re
import logging
from copy import deepcopy

logger = logging.getLogger(__name__)


def find_error_dict_with_code(tests, code):
    return next((test_dict for test_dict in tests if test_dict["code"] == code), None)


def has_not_null_column(sql_statements, **kwargs):
    # TODO: improve to detect that the same column is concerned
    return any(
        re.search("(?<!DROP )NOT NULL", sql) and not sql.startswith("CREATE TABLE")
        for sql in sql_statements
    ) and not any("SET DEFAULT" in sql for sql in sql_statements)


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
        "code": "RENAME_COLUMN",
        "fn": lambda sql, **kw: re.search("ALTER TABLE .* CHANGE", sql)
        or re.search("ALTER TABLE .* RENAME COLUMN", sql),
        "err_msg": "RENAMING columns",
        "mode": "one_liner",
    },
    {
        "code": "ALTER_COLUMN",
        "fn": lambda sql, **kw: re.search("ALTER TABLE .* ALTER COLUMN .* TYPE", sql),
        "err_msg": (
            "ALTERING columns (Could be backward compatible. "
            "You may ignore this migration.)"
        ),
        "mode": "one_liner",
    },
]

mysql_migration_tests = [
    {
        "code": "ALTER_COLUMN",
        "fn": lambda sql, **kw: re.search("ALTER TABLE .* MODIFY .* (?!NULL);?$", sql),
        "mode": "one_liner",
    }
]

postgresql_migration_tests = []

sqlite_migration_tests = [
    {
        "code": "RENAME_TABLE",
        "fn": lambda sql, **kw: re.search("ALTER TABLE .* RENAME TO", sql)
        and "__old" not in sql
        and "new__" not in sql,
    },
    {
        "code": "NOT_NULL",
        "fn": lambda sql_statements, **kw: any(
            re.search("NOT NULL(?! PRIMARY)(?! DEFAULT)", sql) for sql in sql_statements
        )
        and any(
            re.search("ALTER TABLE .* RENAME TO", sql)
            and ("__old" in sql or "new__" in sql)
            for sql in sql_statements
        ),
        "mode": "transaction",
    },
]


def update_migration_tests(base_tests, specific_tests):
    for override_test in specific_tests:
        migration_test_dict = find_error_dict_with_code(
            base_tests, override_test["code"]
        )

        if migration_test_dict is None or not override_test["code"]:
            migration_test_dict = {}
            base_tests.append(migration_test_dict)

        for key in override_test.keys():
            migration_test_dict[key] = override_test[key]
    return base_tests


def get_migration_tests(database_vendor):
    migration_tests = deepcopy(base_migration_tests)

    if "mysql" in database_vendor:
        migration_tests = update_migration_tests(migration_tests, mysql_migration_tests)
    elif "postgre" in database_vendor:
        migration_tests = update_migration_tests(
            migration_tests, postgresql_migration_tests
        )
    elif "sqlite" in database_vendor:
        migration_tests = update_migration_tests(
            migration_tests, sqlite_migration_tests
        )

    return migration_tests


def get_single_line_migration_tests(database_vendor):
    return [
        test
        for test in get_migration_tests(database_vendor)
        if test["mode"] == "one_liner"
    ]


def get_transaction_migration_tests(database_vendor):
    # TODO: improve transaction to detect BEGIN & COMMIT
    return [
        test
        for test in get_migration_tests(database_vendor)
        if test["mode"] == "transaction"
    ]


def build_error_dict(migration_test, sql_statement=""):
    table_search = re.search("TABLE `([^`]*)`", sql_statement, re.IGNORECASE)
    col_search = re.search("COLUMN `([^`]*)`", sql_statement, re.IGNORECASE)
    return {
        "err_msg": migration_test["err_msg"],
        "code": migration_test["code"],
        "table": table_search.group(1) if table_search else None,
        "column": col_search.group(1) if col_search else None,
    }


def analyse_sql_statements(
    sql_statements, database_vendor, exclude_migration_tests=None
):
    exclude_migration_tests = exclude_migration_tests or []
    errors, ignored = [], []
    for statement in sql_statements:
        for test in get_single_line_migration_tests(database_vendor):
            if test["fn"](statement, errors=errors):
                if test["code"] in exclude_migration_tests:
                    logger.debug("Testing {0} -- IGNORED".format(statement))
                    err = build_error_dict(migration_test=test, sql_statement=statement)
                    ignored.append(err)
                else:
                    logger.debug("Testing {0} -- ERROR".format(statement))
                    err = build_error_dict(migration_test=test, sql_statement=statement)
                    errors.append(err)
            else:
                logger.debug("Testing {0} -- PASSED".format(statement))

    for test in get_transaction_migration_tests(database_vendor):
        if test["fn"](sql_statements, errors=errors):
            if test["code"] in exclude_migration_tests:
                logger.debug("Testing {0} -- IGNORED".format(sql_statements))
                err = build_error_dict(migration_test=test)
                ignored.append(err)
            else:
                logger.debug("Testing {0} -- ERROR".format(sql_statements))
                err = build_error_dict(migration_test=test)
                errors.append(err)
        else:
            logger.debug("Testing {0} -- PASSED".format(sql_statements))

    return errors, ignored
