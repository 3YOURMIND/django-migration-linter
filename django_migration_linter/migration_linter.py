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

from __future__ import print_function
import logging
import os
import re
from subprocess import Popen, PIPE
import sys
from . import utils
from .sql_analyser import analyse_sql_statements

logger = logging.getLogger(__name__)


class MigrationLinter(object):
    MIGRATION_FOLDER_NAME = 'migrations'

    def __init__(self, project_path, **kwargs):
        # Verify correctness
        if not utils.is_directory(project_path):
            raise ValueError(
                'The given path {0} does not seem to be a directory.'.format(
                    project_path))
        if not utils.is_django_project(project_path):
            raise ValueError(
                ('The given path {0} does not '
                 'seem to be a django project.').format(project_path))

        # Store parameters and options
        self.django_path = project_path
        self.ignore_name_contains = kwargs.get('ignore_name_contains', None)
        self.ignore_name = kwargs.get('ignore_name', None) or tuple()
        self.include_apps = kwargs.get('include_apps', None)
        self.exclude_apps = kwargs.get('exclude_apps', None)
        self.database = kwargs.get('database', None) or 'default'
        self.python_exe = '{0}/bin/{1}'.format(sys.prefix, 'python') if \
            hasattr(sys, 'real_prefix') else 'python'

        # Initialise counters
        self.nb_valid = 0
        self.nb_ignored = 0
        self.nb_erroneous = 0
        self.nb_total = 0

    def lint_migration(self, app_name, migration_name):
        print('({0}, {1})... '.format(app_name, migration_name), end='')
        self.nb_total += 1

        if self.should_ignore_migration(app_name, migration_name):
            print('IGNORE')
            self.nb_ignored += 1
            return

        sql_statements = self.get_sql(
            app_name, migration_name)
        analysis_result = analyse_sql_statements(
            sql_statements)
        errors = analysis_result['errors']
        if not errors:
            print('OK')
            self.nb_valid += 1
            return

        # Print errors
        print('ERR')
        self.nb_erroneous += 1
        for err in errors:
            error_str = '\t{0}'.format(err['err_msg'])
            if err['table']:
                error_str += ' (table: {0}'.format(err['table'])
                if err['column']:
                    error_str += ', column: {0}'.format(
                        err['column'])
                error_str += ')'
            print(error_str)

    def lint_all_migrations(self, git_commit_id=None):
        # Collect migrations
        if git_commit_id:
            if not utils.is_git_project(self.django_path):
                raise ValueError(
                    ('The given project {0} does not seem '
                     'to be versioned by git.').format(self.django_path))
            migrations = self._gather_migrations_git(git_commit_id)
        else:
            migrations = self._gather_all_migrations()

        # Lint those migrations
        for m in migrations:
            self.lint_migration(*m)

    def print_summary(self):
        print('*** Summary:')
        print(('Valid migrations: {1}/{0} - '
               'erroneous migrations: {2}/{0} - '
               'ignored migrations: {3}/{0}').format(
            self.nb_total,
            self.nb_valid,
            self.nb_erroneous,
            self.nb_ignored))

    @property
    def has_errors(self):
        return self.nb_erroneous > 0

    def get_sql(self, app_name, migration_name):
        """ It would be much faster to call the
        command directly from the code using
        call_command(), but requires the code
        to setup django (by calling django.setup())
        and set the DJANGO_SETTINGS_MODULE.
        However, django is global and doesn't allow
        multiple linter instances to exist at the same time.
        (because they would all just lint the same django project)
        Even if calling a shell is slow and ugly, for now,
        it allows to seperate the instances correctly.
        """
        sqlmigrate_command = (
            'cd {0} && '
            '{1} manage.py sqlmigrate {2} {3} '
            '--database {4}').format(
                self.django_path,
                self.python_exe, app_name, migration_name,
                self.database)
        logger.info('Executing {0}'.format(sqlmigrate_command))
        sqlmigrate_process = Popen(
            sqlmigrate_command, shell=True, stdout=PIPE, stderr=PIPE)

        sql_statements = []
        for line in map(
                utils.clean_bytes_to_str,
                sqlmigrate_process.stdout.readlines()):
            sql_statements.append(line)
        sqlmigrate_process.wait()
        if sqlmigrate_process.returncode != 0:
            _, err = sqlmigrate_process.communicate()
            raise RuntimeError('sqlmigrate command failed {0}'.format(
                err.decode('utf-8')))
        logger.info('Found {0} sql migration lines'.format(len(sql_statements)))
        return sql_statements

    def _gather_migrations_git(self, git_commit_id):
        migrations = []
        # Get changes since specified commit
        git_diff_command = (
            'cd {0} && '
            'git diff --name-only --diff-filter=A {1}').format(
                self.django_path, git_commit_id)
        logger.info('Executing {0}'.format(git_diff_command))
        diff_process = Popen(
            git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in map(
                utils.clean_bytes_to_str, diff_process.stdout.readlines()):
            # Only gather lines that include added migrations
            if re.search(
                    '\/{0}\/.*\.py'.format(self.MIGRATION_FOLDER_NAME),
                    line) and \
                        '__init__' not in line:
                app_name, migration_name = self._split_migration_path(line)
                migrations.append((app_name, migration_name))
        diff_process.wait()

        if diff_process.returncode != 0:
            output = []
            for line in map(
                    utils.clean_bytes_to_str, diff_process.stderr.readlines()):
                output.append(line)
            logger.info("Error while git diff command:\n{}".format(
                "".join(output)))
            raise Exception('Error while executing git diff command')
        return migrations

    def _gather_all_migrations(self):
        migrations = []
        for root, dirs, files in os.walk(self.django_path):
            for file_name in files:
                if os.path.basename(root) == self.MIGRATION_FOLDER_NAME and \
                        file_name.endswith('.py') and \
                        file_name != '__init__.py':
                    full_migration_path = os.path.join(root, file_name)
                    app_name, migration_name = self._split_migration_path(
                        full_migration_path)
                    migrations.append((app_name, migration_name))
        return migrations

    def should_ignore_migration(self, app_name, migration_name):
        return (self.include_apps and
                app_name not in self.include_apps)\
            or (self.exclude_apps and
                app_name in self.exclude_apps)\
            or (self.ignore_name_contains and
                self.ignore_name_contains in migration_name)\
            or (migration_name in self.ignore_name)

    @classmethod
    def _split_migration_path(cls, migration_path):
        decomposed_path = utils.split_path(migration_path)
        for i, p in enumerate(decomposed_path):
            if p == cls.MIGRATION_FOLDER_NAME:
                return (decomposed_path[i-1],
                        os.path.splitext(decomposed_path[i+1])[0])


def _main():
    import argparse
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
        logging.basicConfig(format='%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(message)s')

    folder_name = args.django_folder[0]
    # Create and use linter
    linter = MigrationLinter(
        folder_name,
        ignore_name_contains=args.ignore_name_contains,
        ignore_name=args.ignore_name,
        include_apps=args.include_apps,
        exclude_apps=args.exclude_apps,
        database=args.database)
    linter.lint_all_migrations(
        git_commit_id=args.commit_id)
    linter.print_summary()
    if linter.has_errors:
        sys.exit(1)


if __name__ == '__main__':
    _main()
