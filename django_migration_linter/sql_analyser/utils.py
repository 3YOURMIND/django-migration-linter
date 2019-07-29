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
from copy import deepcopy


def find_error_dict_with_code(tests, code):
    return next((test_dict for test_dict in tests if test_dict["code"] == code), None)


def update_migration_tests(base_tests, specific_tests):
    base_tests = deepcopy(base_tests)
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


def build_error_dict(migration_test, sql_statement):
    table_search = (
        re.search("TABLE `([^`]*)`", sql_statement, re.IGNORECASE)
        if isinstance(sql_statement, str)
        else None
    )
    col_search = (
        re.search("COLUMN `([^`]*)`", sql_statement, re.IGNORECASE)
        if isinstance(sql_statement, str)
        else None
    )
    return {
        "err_msg": migration_test["err_msg"],
        "code": migration_test["code"],
        "table": table_search.group(1) if table_search else None,
        "column": col_search.group(1) if col_search else None,
    }
