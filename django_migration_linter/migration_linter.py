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

import hashlib
import logging
import os
import re
from subprocess import Popen, PIPE

from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS
from django.db.migrations import Migration

from .cache import Cache
from .constants import DEFAULT_CACHE_PATH
from .utils import clean_bytes_to_str, get_migration_abspath, split_migration_path
from .sql_analyser import analyse_sql_statements

logger = logging.getLogger(__name__)

DJANGO_APPS_WITH_MIGRATIONS = ("admin", "auth", "contenttypes", "sessions")


class MigrationLinter(object):
    def __init__(
        self,
        path=None,
        ignore_name_contains=None,
        ignore_name=None,
        include_apps=None,
        exclude_apps=None,
        database=DEFAULT_DB_ALIAS,
        cache_path=DEFAULT_CACHE_PATH,
        no_cache=False,
    ):
        # Store parameters and options
        self.django_path = path
        self.ignore_name_contains = ignore_name_contains
        self.ignore_name = ignore_name or tuple()
        self.include_apps = include_apps
        self.exclude_apps = exclude_apps
        self.database = database or DEFAULT_DB_ALIAS
        self.cache_path = cache_path or DEFAULT_CACHE_PATH
        self.no_cache = no_cache

        # Initialise counters
        self.nb_valid = 0
        self.nb_ignored = 0
        self.nb_erroneous = 0
        self.nb_total = 0

        # Initialise cache. Read from old, write to new to prune old entries.
        if self.should_use_cache():
            self.old_cache = Cache(self.django_path, self.database, self.cache_path)
            self.new_cache = Cache(self.django_path, self.database, self.cache_path)
            self.old_cache.load()

    def should_use_cache(self):
        return self.django_path and not self.no_cache

    def lint_all_migrations(self, git_commit_id=None):
        # Collect migrations
        if git_commit_id:
            migrations = self._gather_migrations_git(git_commit_id)
        else:
            migrations = self._gather_all_migrations()

        # Lint those migrations
        sorted_migrations = sorted(
            migrations, key=lambda migration: (migration.app_label, migration.name)
        )
        for m in sorted_migrations:
            self.lint_migration(m)

        if self.should_use_cache():
            self.new_cache.save()

    def lint_migration(self, migration):
        app_label = migration.app_label
        migration_name = migration.name
        print("({0}, {1})... ".format(app_label, migration_name), end="")
        self.nb_total += 1

        md5hash = self.get_migration_hash(app_label, migration_name)

        if self.should_ignore_migration(app_label, migration_name):
            print("IGNORE")
            self.nb_ignored += 1
            return

        if self.should_use_cache() and md5hash in self.old_cache:
            self.lint_cached_migration(md5hash)
            return

        sql_statements = self.get_sql(app_label, migration_name)
        analysis_result = analyse_sql_statements(sql_statements)
        errors = analysis_result["errors"]

        if analysis_result["ignored"]:
            print("IGNORE")
            self.nb_ignored += 1
            if self.should_use_cache():
                self.new_cache[md5hash] = {"result": "IGNORE"}
            return

        if not errors:
            print("OK")
            self.nb_valid += 1
            if self.should_use_cache():
                self.new_cache[md5hash] = {"result": "OK"}
            return

        print("ERR")
        self.nb_erroneous += 1
        self.print_errors(errors)
        if self.should_use_cache():
            self.new_cache[md5hash] = {"result": "ERR", "errors": errors}

    @staticmethod
    def get_migration_hash(app_label, migration_name):
        hash_md5 = hashlib.md5()
        with open(get_migration_abspath(app_label, migration_name), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def lint_cached_migration(self, md5hash):
        cached_value = self.old_cache[md5hash]
        if cached_value["result"] == "IGNORE":
            print("IGNORE (cached)")
            self.nb_ignored += 1
        elif cached_value["result"] == "OK":
            print("OK (cached)")
            self.nb_valid += 1
        else:
            print("ERR (cached)")
            self.nb_erroneous += 1
            if "errors" in cached_value:
                self.print_errors(cached_value["errors"])

        self.new_cache[md5hash] = cached_value

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

    def get_sql(self, app_label, migration_name):
        logger.info(
            "Calling sqlmigrate command {} {}".format(app_label, migration_name)
        )
        dev_null = open(os.devnull, "w")
        sql_statement = call_command(
            "sqlmigrate",
            app_label,
            migration_name,
            database=self.database,
            stdout=dev_null,
        )
        return sql_statement.splitlines()

    def _gather_migrations_git(self, git_commit_id):
        from django.db.migrations.loader import MIGRATIONS_MODULE_NAME

        migrations = []
        # Get changes since specified commit
        git_diff_command = (
            "cd {0} && git diff --relative --name-only --diff-filter=AR {1}"
        ).format(self.django_path, git_commit_id)
        logger.info("Executing {0}".format(git_diff_command))
        diff_process = Popen(git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in map(clean_bytes_to_str, diff_process.stdout.readlines()):
            # Only gather lines that include added migrations
            if (
                re.search(r"/{0}/.*\.py".format(MIGRATIONS_MODULE_NAME), line)
                and "__init__" not in line
            ):
                app_label, name = split_migration_path(line)
                migrations.append(Migration(name, app_label))
        diff_process.wait()

        if diff_process.returncode != 0:
            output = []
            for line in map(clean_bytes_to_str, diff_process.stderr.readlines()):
                output.append(line)
            logger.error("Error while git diff command:\n{}".format("".join(output)))
            raise Exception("Error while executing git diff command")
        return migrations

    @staticmethod
    def _gather_all_migrations():
        from django.db.migrations.loader import MigrationLoader

        migration_loader = MigrationLoader(connection=None, load=False)
        migration_loader.load_disk()
        # Prune Django apps
        for (app_label, _), migration in migration_loader.disk_migrations.items():
            if app_label not in DJANGO_APPS_WITH_MIGRATIONS:
                yield migration

    def should_ignore_migration(self, app_label, migration_name):
        return (
            (self.include_apps and app_label not in self.include_apps)
            or (self.exclude_apps and app_label in self.exclude_apps)
            or (
                self.ignore_name_contains
                and self.ignore_name_contains in migration_name
            )
            or (migration_name in self.ignore_name)
        )
