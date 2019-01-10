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

from __future__ import print_function
import logging
import os
import re
from subprocess import Popen, PIPE
import sys

from .cache import Cache
from .constants import DEFAULT_CACHE_PATH, MIGRATION_FOLDER_NAME
from .migration import Migration
from .utils import is_directory, is_django_project, clean_bytes_to_str
from .sql_analyser import analyse_sql_statements

logger = logging.getLogger(__name__)


class MigrationLinter(object):
    def __init__(self, project_path, **kwargs):
        # Verify correctness
        if not is_directory(project_path):
            raise ValueError(
                "The given path {0} does not seem to be a directory.".format(
                    project_path
                )
            )
        if not is_django_project(project_path):
            raise ValueError(
                ("The given path {0} does not " "seem to be a django project.").format(
                    project_path
                )
            )

        # Store parameters and options
        self.django_path = project_path
        self.ignore_name_contains = kwargs.get("ignore_name_contains", None)
        self.ignore_name = kwargs.get("ignore_name", None) or tuple()
        self.include_apps = kwargs.get("include_apps", None)
        self.exclude_apps = kwargs.get("exclude_apps", None)
        self.database = kwargs.get("database", None) or "default"
        self.cache_path = kwargs.get("cache_path", None) or DEFAULT_CACHE_PATH
        self.no_cache = kwargs.get("no_cache", None) or False

        self.python_exe = (
            "{0}/bin/{1}".format(sys.prefix, "python")
            if hasattr(sys, "real_prefix")
            else "python"
        )

        # Initialise counters
        self.nb_valid = 0
        self.nb_ignored = 0
        self.nb_erroneous = 0
        self.nb_total = 0

        # Initialise cache. Read from old, write to new to prune old entries.
        self.old_cache = Cache(self.django_path, self.cache_path)
        self.new_cache = Cache(self.django_path, self.cache_path)
        if not self.no_cache:
            self.old_cache.load()

    def lint_migration(self, migration):
        app_name = migration.app_name
        migration_name = migration.name
        print("({0}, {1})... ".format(app_name, migration_name), end="")
        self.nb_total += 1

        md5hash = self.old_cache.md5(migration.abs_path)
        if md5hash in self.old_cache:
            if self.old_cache[md5hash]["result"] == "IGNORE":
                print("IGNORE (cached)")
                self.nb_ignored += 1
            elif self.old_cache[md5hash]["result"] == "OK":
                print("OK (cached)")
                self.nb_valid += 1
            else:
                print("ERR (cached)")
                self.nb_erroneous += 1

            if "errors" in self.old_cache[md5hash]:
                self.print_errors(self.old_cache[md5hash]["errors"])

            self.new_cache[md5hash] = self.old_cache[md5hash]
            return

        if self.should_ignore_migration(app_name, migration_name):
            print("IGNORE")
            self.nb_ignored += 1
            return

        sql_statements = self.get_sql(app_name, migration_name)
        analysis_result = analyse_sql_statements(sql_statements)
        errors = analysis_result["errors"]

        if analysis_result["ignored"]:
            print("IGNORE")
            self.new_cache[md5hash] = {"result": "IGNORE"}
            self.nb_ignored += 1
            return

        if not errors:
            print("OK")
            self.new_cache[md5hash] = {"result": "OK"}
            self.nb_valid += 1
            return

        print("ERR")
        self.new_cache[md5hash] = {"result": "ERR", "errors": errors}
        self.nb_erroneous += 1
        self.print_errors(errors)

    @staticmethod
    def print_errors(errors):
        for err in errors:
            error_str = "\t{0}".format(err["err_msg"])
            if err["table"]:
                error_str += " (table: {0}".format(err["table"])
                if err["column"]:
                    error_str += ", column: {0}".format(err["column"])
                error_str += ")"
            print(error_str)

    def lint_all_migrations(self, git_commit_id=None):
        # Collect migrations
        if git_commit_id:
            migrations = self._gather_migrations_git(git_commit_id)
        else:
            migrations = self._gather_all_migrations()

        # Lint those migrations
        for m in migrations:
            self.lint_migration(m)

        if not self.no_cache:
            self.new_cache.save()

    def print_summary(self):
        print("*** Summary:")
        print(
            (
                "Valid migrations: {1}/{0} - "
                "erroneous migrations: {2}/{0} - "
                "ignored migrations: {3}/{0}"
            ).format(self.nb_total, self.nb_valid, self.nb_erroneous, self.nb_ignored)
        )

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
            "cd {0} && {1} manage.py sqlmigrate {2} {3} " "--database {4}"
        ).format(
            self.django_path, self.python_exe, app_name, migration_name, self.database
        )
        logger.info("Executing {0}".format(sqlmigrate_command))
        sqlmigrate_process = Popen(
            sqlmigrate_command, shell=True, stdout=PIPE, stderr=PIPE
        )

        sql_statements = []
        for line in map(clean_bytes_to_str, sqlmigrate_process.stdout.readlines()):
            sql_statements.append(line)
        sqlmigrate_process.wait()
        if sqlmigrate_process.returncode != 0:
            _, err = sqlmigrate_process.communicate()
            raise RuntimeError(
                "sqlmigrate command failed {0}".format(err.decode("utf-8"))
            )
        logger.info("Found {0} sql migration lines".format(len(sql_statements)))
        return sql_statements

    def _get_git_root(self):
        git_root = self.django_path
        command = "cd {0} && git rev-parse --show-toplevel".format(self.django_path)
        logger.info("Executing {0}".format(command))
        diff_process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in map(clean_bytes_to_str, diff_process.stdout.readlines()):
            git_root = line
        diff_process.wait()

        if diff_process.returncode != 0:
            output = []
            for line in map(clean_bytes_to_str, diff_process.stderr.readlines()):
                output.append(line)
            logger.error(
                "Error while git rev-parse command:\n{}".format("".join(output))
            )
            raise Exception("Error while executing git rev-parse command")
        return git_root

    def _gather_migrations_git(self, git_commit_id):
        migrations = []
        git_root = self._get_git_root()
        # Get changes since specified commit
        git_diff_command = (
            "cd {0} && git diff --name-only --diff-filter=A {1}"
        ).format(self.django_path, git_commit_id)
        logger.info("Executing {0}".format(git_diff_command))
        diff_process = Popen(git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in map(clean_bytes_to_str, diff_process.stdout.readlines()):
            # Only gather lines that include added migrations
            if (
                re.search(r"\/{0}\/.*\.py".format(MIGRATION_FOLDER_NAME), line)
                and "__init__" not in line
            ):
                migrations.append(Migration(os.path.join(git_root, line)))
        diff_process.wait()

        if diff_process.returncode != 0:
            output = []
            for line in map(clean_bytes_to_str, diff_process.stderr.readlines()):
                output.append(line)
            logger.error("Error while git diff command:\n{}".format("".join(output)))
            raise Exception("Error while executing git diff command")
        return migrations

    def _gather_all_migrations(self):
        migrations = []
        for root, dirs, files in os.walk(self.django_path):
            for file_name in sorted(files):
                if (
                    os.path.basename(root) == MIGRATION_FOLDER_NAME
                    and file_name.endswith(".py")
                    and file_name != "__init__.py"
                ):
                    full_migration_path = os.path.join(root, file_name)
                    migrations.append(Migration(full_migration_path))
        return migrations

    def should_ignore_migration(self, app_name, migration_name):
        return (
            (self.include_apps and app_name not in self.include_apps)
            or (self.exclude_apps and app_name in self.exclude_apps)
            or (
                self.ignore_name_contains
                and self.ignore_name_contains in migration_name
            )
            or (migration_name in self.ignore_name)
        )


def _main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Detect backward incompatible django migrations."
    )
    parser.add_argument(
        "django_folder",
        metavar="DJANGO_FOLDER",
        type=str,
        nargs=1,
        help="the path to the django project",
    )
    parser.add_argument(
        "commit_id",
        metavar="GIT_COMMIT_ID",
        type=str,
        nargs="?",
        help=(
            "if specified, only migrations since this commit "
            "will be taken into account. If not specified, "
            "the initial repo commit will be used"
        ),
    )
    parser.add_argument(
        "--ignore-name-contains",
        type=str,
        nargs="?",
        help="ignore migrations containing this name",
    )
    parser.add_argument(
        "--ignore-name",
        type=str,
        nargs="*",
        help="ignore migrations with exactly one of these names",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print more information during execution",
    )
    parser.add_argument(
        "--database",
        type=str,
        nargs="?",
        help=(
            "specify the database for which to generate the SQL. " "Defaults to default"
        ),
    )

    cache_group = parser.add_mutually_exclusive_group(required=False)
    cache_group.add_argument(
        "--cache-path",
        type=str,
        help="specify a directory that should be used to" "store cache-files in.",
    )
    cache_group.add_argument(
        "--no-cache", action="store_true", help="don't use a cache"
    )

    incl_excl_group = parser.add_mutually_exclusive_group(required=False)
    incl_excl_group.add_argument(
        "--include-apps",
        type=str,
        nargs="*",
        help="check only migrations that are in the specified django apps",
    )
    incl_excl_group.add_argument(
        "--exclude-apps",
        type=str,
        nargs="*",
        help="ignore migrations that are in the specified django apps",
    )

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)
    else:
        logging.basicConfig(format="%(message)s")

    folder_name = args.django_folder[0]
    # Create and use linter
    linter = MigrationLinter(
        folder_name,
        ignore_name_contains=args.ignore_name_contains,
        ignore_name=args.ignore_name,
        include_apps=args.include_apps,
        exclude_apps=args.exclude_apps,
        database=args.database,
        cache_path=args.cache_path,
        no_cache=args.no_cache,
    )
    linter.lint_all_migrations(git_commit_id=args.commit_id)
    linter.print_summary()
    if linter.has_errors:
        sys.exit(1)


if __name__ == "__main__":
    _main()
