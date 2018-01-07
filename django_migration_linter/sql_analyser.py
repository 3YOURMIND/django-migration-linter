# Copyright 2018 3YOURMIND GmbH

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
import logging as log


def has_default(sql, **kwargs):
    if re.search('SET DEFAULT', sql) and kwargs['errors']:
        err = next(err
                   for err in kwargs['errors']
                   if err['code'] == 'NOT_NULL')
        if err:
            log.info(
                ('Found a NOT_NULL error in migration, '
                 'but it has a default value added: {}').format(err))
            kwargs['errors'].remove(err)

    return False  # Never fails


migration_tests = (
    {
        'code': 'NOT_NULL',
        'fn': lambda sql, **kw: re.search('NOT NULL', sql) and
                not re.search('CREATE TABLE', sql),
        'err_msg': 'NOT NULL constraint on columns'
    }, {
        'code': 'DROP_COLUMN',
        'fn': lambda sql, **kw: re.search('DROP COLUMN', sql),
        'err_msg': 'DROPPING columns'
    }, {
        'code': 'RENAME_COLUMN',
        'fn': lambda sql, **kw: re.search('ALTER TABLE .* CHANGE', sql) or
                re.search('ALTER TABLE .* RENAME COLUMN', sql),
        'err_msg': 'RENAMING columns'
    }, {
        'code': 'RENAME_TABLE',
        'fn': lambda sql, **kw: re.search('RENAME TABLE', sql) or
                re.search('ALTER TABLE .* RENAME TO', sql),
        'err_msg': 'RENAMING tables'
    }, {
        'code': '',
        'fn': has_default,
        'err_msg': ''
    }
)


def analyse_sql_statements(sql_statements):
    errors = []
    for statement in sql_statements:
        for test in migration_tests:
            if test['fn'](statement, errors=errors):
                log.info('Testing {0} -- ERROR'.format(statement))
                table_search = re.search(
                    'TABLE `([^`]*)`', statement, re.IGNORECASE)
                col_search = re.search(
                    'COLUMN `([^`]*)`', statement, re.IGNORECASE)
                err = {
                    'err_msg': test['err_msg'],
                    'code': test['code'],
                    'table': table_search.group(1) if table_search else None,
                    'column': col_search.group(1) if col_search else None
                }
                errors.append(err)
            else:
                log.info('Testing {0} -- PASSED'.format(statement))
    return {
        'errors': errors,
    }
