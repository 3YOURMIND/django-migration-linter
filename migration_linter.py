# Copyright 2017 3YOURMIN GmbH

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
import os
import re
from subprocess import Popen, PIPE
import sys


class MigrationLinter:
    MIGRATION_FOLDER_NAME = 'migrations'

    migration_tests = (
        {
            'fn': lambda sql: re.search('NOT NULL', sql),
            'err_msg': 'NOT NULL constraint on columns'
        }, {
            'fn': lambda sql: re.search('DROP COLUMN', sql),
            'err_msg': 'DROPPING columns'
        }, {
            'fn': lambda sql: re.search('ADD COLUMN .* DEFAULT', sql),
            'err_msg': 'ADD columns with default'
        }, {
            'fn': lambda sql: re.search('ALTER TABLE .* CHANGE', sql) or re.search('ALTER TABLE .* RENAME COLUMN', sql),  # mysql or postgre
            'err_msg': 'RENAMING columns'
        }, {
            'fn': lambda sql: re.search('RENAME TABLE', sql) or re.search('ALTER TABLE .* RENAME TO', sql),  # mysql or postgre
            'err_msg': 'RENAMING tables'
        }
    )

    def __init__(self, django_folder, commit_id=None, **kwargs):
        self.location = django_folder
        self.commit_id = commit_id
        self.ignore_name_contains = kwargs.get('ignore_name_contains', None)
        self.include_apps = kwargs.get('include_apps', None)
        self.exclude_apps = kwargs.get('exclude_apps', None)

        self.changed_migration_files = []
        self._gather_migrations()

    def _gather_migrations(self):
        # Find (one of) the initial commits
        if not self.commit_id:
            git_init_cmd = 'cd {0} && git rev-list HEAD | tail -n 1'.format(self.location)
            process = Popen(git_init_cmd, shell=True, stdout=PIPE, stderr=PIPE)
            for line in process.stdout.readlines():
                self.commit_id = line.strip()
                break
            process.wait()

        # Get changes since specified commit
        git_diff_command = 'cd {0} && git diff --name-only {1}'.format(self.location, self.commit_id)
        diff_process = Popen(git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in diff_process.stdout.readlines():
            # Only gather lines that include migrations
            if re.search('\/{0}\/.*\.py'.format(self.MIGRATION_FOLDER_NAME), line):
                self.changed_migration_files.append(line.strip())
        diff_process.wait()
        if diff_process.returncode != 0:
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
                sql_statements = self.django_sqlmigrate(app_name, migration_name)
                errors = set()
                for statement in sql_statements:
                    is_valid, err_msg = self._test_sql_statement_for_backward_incompatibility(statement)
                    if not is_valid:
                        errors.add(err_msg)
                if not errors:
                    print('OK')
                    nb_valid += 1
                else:
                    print('ERR')
                    nb_erroneous += 1
                    for err in errors:
                        print('\t' + err)
        print('*** Summary:')
        print('Valid migrations: {0}/{1} - erroneous migrations: {2}/{1} - ignored migrations: {3}/{1}'.format(nb_valid, len(self.changed_migration_files), nb_erroneous, nb_ignore))
        return nb_erroneous > 0

    @classmethod
    def _split_migration_path(cls, migration_path):
        decomposed_path = split_path(migration_path)
        for i, p in enumerate(decomposed_path):
            if p == cls.MIGRATION_FOLDER_NAME:
                return decomposed_path[i-1], os.path.splitext(decomposed_path[i+1])[0]

    def should_ignore_migration(self, app_name, migration_name):
        return (self.include_apps and app_name not in self.include_apps)\
            or (self.exclude_apps and app_name in self.exclude_apps)\
            or (self.ignore_name_contains and self.ignore_name_contains in migration_name)

    def django_sqlmigrate(self, app_name, migration_name):
        git_diff_command = 'cd {0} && python manage.py sqlmigrate {1} {2}'.format(self.location, app_name, migration_name)
        diff_process = Popen(git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        sql_statements = []
        for line in diff_process.stdout.readlines():
            if not line.startswith('--'):  # Do not take sql comments into account
                sql_statements.append(line.strip())
        diff_process.wait()
        return sql_statements

    def _test_sql_statement_for_backward_incompatibility(self, sql_statement):
        for test in self.migration_tests:
            if test['fn'](sql_statement):
                return False, test['err_msg']
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
        print("The passed folder doesn't seem to be a django project (no manage.py found).")
        return False
    git_folder = os.path.join(folder, '.git')
    if not os.path.isdir(git_folder):
        print("The passed folder doesn't seem to versioned by git (no .git/ folder found).")
        return False
    return True


def split_path(path):
    a, b = os.path.split(path)
    return (split_path(a) if len(a) > 0 else []) + [b]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Detect backward incompatible django migrations.')
    parser.add_argument('django_folder', metavar='DJANGO_FOLDER', type=str, nargs=1, help='the path to the django project')
    parser.add_argument('commit_id', metavar='GIT_COMMIT_ID', type=str, nargs='?', help='if specified, only migrations since this commit will be taken into account. If not specified, the initial repo commit will be used')
    parser.add_argument('--ignore-name-contains', type=str, nargs='?', help='ignore migrations containing this name')
    incl_excl_group = parser.add_mutually_exclusive_group(required=False)
    incl_excl_group.add_argument('--include-apps', type=str, nargs='*', help='check only migrations that are in the specified django apps')
    incl_excl_group.add_argument('--exclude-apps', type=str, nargs='*', help='ignore migrations that are in the specified django apps')

    args = parser.parse_args()

    folder_name = args.django_folder[0]
    if valid_folder(folder_name):
        linter = MigrationLinter(folder_name, args.commit_id, ignore_name_contains=args.ignore_name_contains, include_apps=args.include_apps, exclude_apps=args.exclude_apps)
        has_errors = linter.lint_migrations()
        if has_errors:
            sys.exit(1)
    else:
        sys.exit(1)
