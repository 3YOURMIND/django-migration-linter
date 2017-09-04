# Copyright 2017 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import argparse
import logging as log
import os
import re
from subprocess import Popen, PIPE
import sys


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


class MigrationLinter:
    MIGRATION_FOLDER_NAME = 'migrations'

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

    def __init__(self, django_folder, commit_id=None, **kwargs):
        self.location = django_folder
        self.commit_id = commit_id
        self.ignore_name_contains = kwargs.get('ignore_name_contains', None)
        self.ignore_name = kwargs.get('ignore_name', None) or tuple()
        self.include_apps = kwargs.get('include_apps', None)
        self.exclude_apps = kwargs.get('exclude_apps', None)
        self.database = kwargs.get('database', None) or 'default'

        self.changed_migration_files = []
        self._gather_migrations()

    def _gather_migrations(self):
        # Find (one of) the initial commits
        if not self.commit_id:
            git_init_cmd = 'cd {0} && git rev-list HEAD | tail -n 1'.format(
                self.location)
            process = Popen(git_init_cmd, shell=True, stdout=PIPE, stderr=PIPE)
            for line in process.stdout.readlines():
                self.commit_id = line.strip()
                break
            process.wait()
        log.info('Operating until git identifier {0}'.format(self.commit_id))

        # Get changes since specified commit
        git_diff_command = 'cd {0} && git diff --name-only {1}'.format(
            self.location, self.commit_id)
        log.info('Executing {0}'.format(git_diff_command))
        diff_process = Popen(
            git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in diff_process.stdout.readlines():
            # Only gather lines that include migrations
            if re.search(
                    '\/{0}\/.*\.py'.format(self.MIGRATION_FOLDER_NAME),
                    line) and \
                        '__init__' not in line:
                self.changed_migration_files.append(line.strip())
        diff_process.wait()
        if diff_process.returncode != 0:
            output = []
            for line in diff_process.stderr.readlines():
                output.append(line)
            log.info("Error while git diff command:\n{}".format(
                "".join(output)))
            raise Exception('Error while executing git diff command')

    def lint_migrations(self):
        nb_valid = 0
        nb_erroneous = 0
        nb_ignore = 0
        for migration in self.changed_migration_files:
            app_name, migration_name = self._split_migration_path(migration)
            print('{0}... '.format(migration), end='')
            if self.should_ignore_migration(app_name, migration_name):
                print('IGNORE')
                nb_ignore += 1
            else:
                sql_statements = self.django_sqlmigrate(
                    app_name, migration_name)
                errors = []
                for statement in sql_statements:
                    is_valid, err = \
                        self._test_sql_statement_for_backward_incompatibility(
                            statement, errors)
                    if not is_valid:
                        errors.append(err)
                if not errors:
                    print('OK')
                    nb_valid += 1
                else:
                    print('ERR')
                    nb_erroneous += 1
                    for err in errors:
                        error_str = '\t{0}'.format(err['err_msg'])
                        if err['table']:
                            error_str += ' (table: {0}'.format(err['table'])
                            if err['column']:
                                error_str += ', column: {0}'.format(
                                    err['column'])
                            error_str += ')'
                        print(error_str)
        print('*** Summary:')
        print(('Valid migrations: {0}/{1} - '
               'erroneous migrations: {2}/{1} - '
               'ignored migrations: {3}/{1}').format(
            nb_valid,
            len(self.changed_migration_files),
            nb_erroneous,
            nb_ignore))
        return nb_erroneous > 0

    @classmethod
    def _split_migration_path(cls, migration_path):
        decomposed_path = split_path(migration_path)
        for i, p in enumerate(decomposed_path):
            if p == cls.MIGRATION_FOLDER_NAME:
                return (decomposed_path[i-1],
                        os.path.splitext(decomposed_path[i+1])[0])

    def should_ignore_migration(self, app_name, migration_name):
        return (self.include_apps and
                app_name not in self.include_apps)\
            or (self.exclude_apps and
                app_name in self.exclude_apps)\
            or (self.ignore_name_contains and
                self.ignore_name_contains in migration_name)\
            or (migration_name in self.ignore_name)

    def django_sqlmigrate(self, app_name, migration_name):
        git_diff_command = (
            'cd {0} && '
            'python manage.py sqlmigrate {1} {2} '
            '--database {3}').format(
            self.location, app_name, migration_name, self.database)
        log.info('Executing {0}'.format(git_diff_command))
        diff_process = Popen(
            git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        sql_statements = []
        for line in diff_process.stdout.readlines():
            if not line.startswith('--'):  # Ignore comments
                sql_statements.append(line.strip())
        diff_process.wait()
        if diff_process.returncode != 0:
            raise RuntimeError('sqlmigrate command failed')
        log.info('Found {0} sql migration lines'.format(len(sql_statements)))
        return sql_statements

    def _test_sql_statement_for_backward_incompatibility(
            self, sql_statement, errors):
        for test in self.migration_tests:
            if test['fn'](sql_statement, errors=errors):
                log.info('Testing {0} -- ERROR'.format(sql_statement))
                table_search = re.search(
                    'TABLE `([^`]*)`', sql_statement, re.IGNORECASE)
                col_search = re.search(
                    'COLUMN `([^`]*)`', sql_statement, re.IGNORECASE)
                err = {
                    'err_msg': test['err_msg'],
                    'code': test['code'],
                    'table': table_search.group(1) if table_search else None,
                    'column': col_search.group(1) if col_search else None
                }
                return False, err
        log.info('Testing {0} -- PASSED'.format(sql_statement))
        return True, None


def valid_folder(folder):
    """Verify folder exists,
    folder is a django project
    and folder is git versioned
    """
    if not os.path.isdir(folder):
        print("The passed argument doesn't seem to be a folder.")
        return False
    django_manage_file = os.path.join(folder, 'manage.py')
    if not os.path.isfile(django_manage_file):
        print(("The passed folder doesn't seem to be a "
               "django project (no manage.py found)."))
        return False
    git_folder = os.path.join(folder, '.git')
    if not os.path.isdir(git_folder):
        print(("The passed folder doesn't seem to be "
               "versioned by git (no .git/ folder found)."))
        return False
    return True


def split_path(path):
    a, b = os.path.split(path)
    return (split_path(a) if len(a) > 0 else []) + [b]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Detect backward incompatible django migrations.')
    parser.add_argument(
        'django_folder',
        metavar='DJANGO_FOLDER',
        type=str,
        nargs=1,
        help='the path to the django project')
    parser.add_argument(
        'commit_id',
        metavar='GIT_COMMIT_ID',
        type=str, nargs='?',
        help=('if specified, only migrations since this commit '
              'will be taken into account. If not specified, '
              'the initial repo commit will be used'))
    parser.add_argument(
        '--ignore-name-contains',
        type=str,
        nargs='?',
        help='ignore migrations containing this name')
    parser.add_argument(
        '--ignore-name',
        type=str,
        nargs='*',
        help='ignore migrations with exactly one of these names')
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='print more information during execution')
    parser.add_argument(
        '--database',
        type=str,
        nargs='?',
        help=('specify the database for which to generate the SQL. '
              'Defaults to default'))

    incl_excl_group = parser.add_mutually_exclusive_group(
        required=False)
    incl_excl_group.add_argument(
        '--include-apps',
        type=str,
        nargs='*',
        help='check only migrations that are in the specified django apps')
    incl_excl_group.add_argument(
        '--exclude-apps',
        type=str,
        nargs='*',
        help='ignore migrations that are in the specified django apps')

    args = parser.parse_args()
    if args.verbose:
        log.basicConfig(format='%(message)s', level=log.DEBUG)
    else:
        log.basicConfig(format='%(message)s')

    folder_name = args.django_folder[0]
    if valid_folder(folder_name):
        linter = MigrationLinter(
            folder_name,
            args.commit_id,
            ignore_name_contains=args.ignore_name_contains,
            ignore_name=args.ignore_name,
            include_apps=args.include_apps,
            exclude_apps=args.exclude_apps,
            database=args.database)
        has_errors = linter.lint_migrations()
        if has_errors:
            sys.exit(1)
    else:
        sys.exit(1)
