from __future__ import print_function

import hashlib
import inspect
import logging
import os
import re
from enum import Enum, unique
from subprocess import PIPE, Popen

from django.conf import settings
from django.core.management import call_command
from django.db import DEFAULT_DB_ALIAS, ProgrammingError, connections
from django.db.migrations import RunPython, RunSQL

from .cache import Cache
from .constants import (
    DEFAULT_CACHE_PATH,
    DJANGO_APPS_WITH_MIGRATIONS,
    EXPECTED_DATA_MIGRATION_ARGS,
)
from .operations import IgnoreMigration
from .sql_analyser import analyse_sql_statements, get_sql_analyser_class
from .utils import clean_bytes_to_str, get_migration_abspath, split_migration_path

logger = logging.getLogger("django_migration_linter")


@unique
class MessageType(Enum):
    OK = "ok"
    IGNORE = "ignore"
    WARNING = "warning"
    ERROR = "error"

    @staticmethod
    def values():
        return list(map(lambda c: c.value, MessageType))


class MigrationLinter(object):
    def __init__(
        self,
        path=None,
        ignore_name_contains=None,
        ignore_name=None,
        include_name_contains=None,
        include_name=None,
        include_apps=None,
        exclude_apps=None,
        database=DEFAULT_DB_ALIAS,
        cache_path=DEFAULT_CACHE_PATH,
        no_cache=False,
        only_applied_migrations=False,
        only_unapplied_migrations=False,
        exclude_migration_tests=None,
        quiet=None,
        warnings_as_errors=False,
        no_output=False,
        analyser_string=None,
    ):
        # Store parameters and options
        self.django_path = path
        self.ignore_name_contains = ignore_name_contains
        self.ignore_name = ignore_name or tuple()
        self.include_name_contains = include_name_contains
        self.include_name = include_name or tuple()
        self.include_apps = include_apps
        self.exclude_apps = exclude_apps
        self.exclude_migration_tests = exclude_migration_tests or []
        self.database = database or DEFAULT_DB_ALIAS
        self.cache_path = cache_path or DEFAULT_CACHE_PATH
        self.no_cache = no_cache
        self.only_applied_migrations = only_applied_migrations
        self.only_unapplied_migrations = only_unapplied_migrations
        self.quiet = quiet or []
        self.warnings_as_errors = warnings_as_errors
        self.no_output = no_output
        self.sql_analyser_class = get_sql_analyser_class(
            settings.DATABASES[self.database]["ENGINE"],
            analyser_string=analyser_string,
        )

        # Initialise counters
        self.reset_counters()

        # Initialise cache. Read from old, write to new to prune old entries.
        if self.should_use_cache():
            self.old_cache = Cache(self.django_path, self.database, self.cache_path)
            self.new_cache = Cache(self.django_path, self.database, self.cache_path)
            self.old_cache.load()

        # Initialise migrations
        from django.db.migrations.loader import MigrationLoader

        self.migration_loader = MigrationLoader(
            connection=connections[self.database], load=True
        )

    def reset_counters(self):
        self.nb_valid = 0
        self.nb_ignored = 0
        self.nb_warnings = 0
        self.nb_erroneous = 0
        self.nb_total = 0

    def should_use_cache(self):
        return self.django_path and not self.no_cache

    def lint_all_migrations(
        self,
        app_label=None,
        migration_name=None,
        git_commit_id=None,
        migrations_file_path=None,
    ):
        # Collect migrations
        migrations_list = self.read_migrations_list(migrations_file_path)
        if git_commit_id:
            migrations = self._gather_migrations_git(git_commit_id, migrations_list)
        else:
            migrations = self._gather_all_migrations(migrations_list)

        # Lint those migrations
        sorted_migrations = sorted(
            migrations, key=lambda migration: (migration.app_label, migration.name)
        )

        specific_target_migration = (
            self.migration_loader.get_migration_by_prefix(app_label, migration_name)
            if app_label and migration_name
            else None
        )

        for m in sorted_migrations:
            if app_label and migration_name:
                if m == specific_target_migration:
                    self.lint_migration(m)
            elif app_label:
                if m.app_label == app_label:
                    self.lint_migration(m)
            else:
                self.lint_migration(m)

        if self.should_use_cache():
            self.new_cache.save()

    def lint_migration(self, migration):
        app_label = migration.app_label
        migration_name = migration.name
        operations = migration.operations
        self.nb_total += 1

        md5hash = self.get_migration_hash(app_label, migration_name)

        if self.should_ignore_migration(app_label, migration_name, operations):
            self.print_linting_msg(
                app_label, migration_name, "IGNORE", MessageType.IGNORE
            )
            self.nb_ignored += 1
            return

        if self.should_use_cache() and md5hash in self.old_cache:
            self.lint_cached_migration(app_label, migration_name, md5hash)
            return

        sql_statements = self.get_sql(app_label, migration_name)
        errors, ignored, warnings = analyse_sql_statements(
            self.sql_analyser_class,
            sql_statements,
            self.exclude_migration_tests,
        )

        err, ignored_data, warnings_data = self.analyse_data_migration(migration)
        if err:
            errors += err
        if ignored_data:
            ignored += ignored_data
        if warnings_data:
            warnings += warnings_data

        if self.warnings_as_errors:
            errors += warnings
            warnings = []

        # Fixme: have a more generic approach to handling errors/warnings/ignored/ok?
        if errors:
            self.print_linting_msg(app_label, migration_name, "ERR", MessageType.ERROR)
            self.nb_erroneous += 1
            self.print_errors(errors)
            if warnings:
                self.print_warnings(warnings)
            value_to_cache = {"result": "ERR", "errors": errors, "warnings": warnings}
        elif warnings:
            self.print_linting_msg(
                app_label, migration_name, "WARNING", MessageType.WARNING
            )
            self.nb_warnings += 1
            self.print_warnings(warnings)
            value_to_cache = {"result": "WARNING", "warnings": warnings}
            # Fixme: not displaying ignored errors, when
        else:
            if ignored:
                self.print_linting_msg(
                    app_label, migration_name, "OK (ignored)", MessageType.IGNORE
                )
                self.print_errors(ignored)
            else:
                self.print_linting_msg(app_label, migration_name, "OK", MessageType.OK)
            self.nb_valid += 1
            value_to_cache = {"result": "OK"}

        if self.should_use_cache():
            self.new_cache[md5hash] = value_to_cache

    @staticmethod
    def get_migration_hash(app_label, migration_name):
        hash_md5 = hashlib.md5()
        with open(get_migration_abspath(app_label, migration_name), "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def lint_cached_migration(self, app_label, migration_name, md5hash):
        cached_value = self.old_cache[md5hash]
        if cached_value["result"] == "IGNORE":
            self.print_linting_msg(
                app_label, migration_name, "IGNORE (cached)", MessageType.IGNORE
            )
            self.nb_ignored += 1
        elif cached_value["result"] == "OK":
            self.print_linting_msg(
                app_label, migration_name, "OK (cached)", MessageType.OK
            )
            self.nb_valid += 1
        elif cached_value["result"] == "WARNING":
            self.print_linting_msg(
                app_label, migration_name, "WARNING (cached)", MessageType.WARNING
            )
            self.nb_warnings += 1
            self.print_warnings(cached_value["warnings"])
        else:
            self.print_linting_msg(
                app_label, migration_name, "ERR (cached)", MessageType.ERROR
            )
            self.nb_erroneous += 1
            if "errors" in cached_value:
                self.print_errors(cached_value["errors"])
            if "warnings" in cached_value and cached_value["warnings"]:
                self.print_warnings(cached_value["warnings"])

        self.new_cache[md5hash] = cached_value

    def print_linting_msg(self, app_label, migration_name, msg, lint_result):
        if lint_result.value in self.quiet:
            return
        if not self.no_output:
            print("({0}, {1})... {2}".format(app_label, migration_name, msg))

    def print_errors(self, errors):
        if MessageType.ERROR.value in self.quiet:
            return
        for err in errors:
            error_str = "\t{0}".format(err["msg"])
            if err.get("table"):
                error_str += " (table: {0}".format(err["table"])
                if err.get("column"):
                    error_str += ", column: {0}".format(err["column"])
                error_str += ")"
            if not self.no_output:
                print(error_str)

    def print_warnings(self, warnings):
        if MessageType.WARNING.value in self.quiet:
            return

        for warning_details in warnings:
            warn_str = "\t{}".format(warning_details["msg"])
            if not self.no_output:
                print(warn_str)

    def print_summary(self):
        if self.no_output:
            return
        print("*** Summary ***")
        print("Valid migrations: {}/{}".format(self.nb_valid, self.nb_total))
        print("Erroneous migrations: {}/{}".format(self.nb_erroneous, self.nb_total))
        print("Migrations with warnings: {}/{}".format(self.nb_warnings, self.nb_total))
        print("Ignored migrations: {}/{}".format(self.nb_ignored, self.nb_total))

    @property
    def has_errors(self):
        return self.nb_erroneous > 0

    def get_sql(self, app_label, migration_name):
        logger.info(
            "Calling sqlmigrate command {} {}".format(app_label, migration_name)
        )
        dev_null = open(os.devnull, "w")
        try:
            sql_statement = call_command(
                "sqlmigrate",
                app_label,
                migration_name,
                database=self.database,
                stdout=dev_null,
            )
        except (ValueError, ProgrammingError):
            logger.warning(
                (
                    "Error while executing sqlmigrate on (%s, %s). "
                    "Continuing execution with empty SQL."
                ),
                app_label,
                migration_name,
            )
            sql_statement = ""
        return sql_statement.splitlines()

    @staticmethod
    def is_migration_file(filename):
        from django.db.migrations.loader import MIGRATIONS_MODULE_NAME

        return (
            re.search(r"/{0}/.*\.py".format(MIGRATIONS_MODULE_NAME), filename)
            and "__init__" not in filename
        )

    @classmethod
    def read_migrations_list(cls, migrations_file_path):
        """
        Returning an empty list is different from returning None here.
        None: no file was specified and we should consider all migrations
        Empty list: no migration found in the file and we should consider no migration
        """
        if not migrations_file_path:
            return None

        migrations = []
        try:
            with open(migrations_file_path, "r") as file:
                for line in file:
                    if cls.is_migration_file(line):
                        app_label, name = split_migration_path(line)
                        migrations.append((app_label, name))
        except IOError:
            logger.exception("Migrations list path not found %s", migrations_file_path)
            raise Exception("Error while reading migrations list file")

        if not migrations:
            logger.info(
                "No valid migration paths found in the migrations file %s",
                migrations_file_path,
            )
        return migrations

    def _gather_migrations_git(self, git_commit_id, migrations_list=None):
        migrations = []
        # Get changes since specified commit
        git_diff_command = (
            "cd {0} && git diff --relative --name-only --diff-filter=AR {1}"
        ).format(self.django_path, git_commit_id)
        logger.info("Executing {0}".format(git_diff_command))
        diff_process = Popen(git_diff_command, shell=True, stdout=PIPE, stderr=PIPE)
        for line in map(clean_bytes_to_str, diff_process.stdout.readlines()):
            # Only gather lines that include added migrations
            if self.is_migration_file(line):
                app_label, name = split_migration_path(line)
                if migrations_list is None or (app_label, name) in migrations_list:
                    if (app_label, name) in self.migration_loader.disk_migrations:
                        migration = self.migration_loader.disk_migrations[
                            app_label, name
                        ]
                        migrations.append(migration)
                    else:
                        logger.info(
                            "Found migration file (%s, %s) "
                            "that is not present in loaded migration.",
                            app_label,
                            name,
                        )
        diff_process.wait()

        if diff_process.returncode != 0:
            output = []
            for line in map(clean_bytes_to_str, diff_process.stderr.readlines()):
                output.append(line)
            logger.error("Error while git diff command:\n{}".format("".join(output)))
            raise Exception("Error while executing git diff command")
        return migrations

    def _gather_all_migrations(self, migrations_list=None):
        for (
            (app_label, name),
            migration,
        ) in self.migration_loader.disk_migrations.items():
            if app_label not in DJANGO_APPS_WITH_MIGRATIONS:  # Prune Django apps
                if migrations_list is None or (app_label, name) in migrations_list:
                    yield migration

    def should_ignore_migration(self, app_label, migration_name, operations=()):
        return (
            (self.include_apps and app_label not in self.include_apps)
            or (self.exclude_apps and app_label in self.exclude_apps)
            or any(isinstance(o, IgnoreMigration) for o in operations)
            or (
                self.ignore_name_contains
                and self.ignore_name_contains in migration_name
            )
            or (
                self.include_name_contains
                and self.include_name_contains not in migration_name
            )
            or (migration_name in self.ignore_name)
            or (self.include_name and migration_name not in self.include_name)
            or (
                self.only_applied_migrations
                and (app_label, migration_name)
                not in self.migration_loader.applied_migrations
            )
            or (
                self.only_unapplied_migrations
                and (app_label, migration_name)
                in self.migration_loader.applied_migrations
            )
        )

    def analyse_data_migration(self, migration):
        errors = []
        ignored = []
        warnings = []

        for operation in migration.operations:
            if isinstance(operation, RunPython):
                op_errors, op_ignored, op_warnings = self.lint_runpython(operation)
            elif isinstance(operation, RunSQL):
                op_errors, op_ignored, op_warnings = self.lint_runsql(operation)
            else:
                op_errors, op_ignored, op_warnings = [], [], []

            if op_errors:
                errors += op_errors
            if op_ignored:
                ignored += op_ignored
            if op_warnings:
                warnings += op_warnings

        return errors, ignored, warnings

    def lint_runpython(self, runpython):
        function_name = runpython.code.__name__
        error = []
        ignored = []
        warning = []

        # Detect warning on missing reverse operation
        if not runpython.reversible:
            issue = {
                "code": "RUNPYTHON_REVERSIBLE",
                "msg": "'{}': RunPython data migration is not reversible".format(
                    function_name
                ),
            }
            if issue["code"] in self.exclude_migration_tests:
                ignored.append(issue)
            else:
                warning.append(issue)

        # Detect warning for argument naming convention
        args_spec = inspect.getfullargspec(runpython.code)
        if tuple(args_spec.args) != EXPECTED_DATA_MIGRATION_ARGS:
            issue = {
                "code": "RUNPYTHON_ARGS_NAMING_CONVENTION",
                "msg": (
                    "'{}': By convention, "
                    "RunPython names the two arguments: apps, schema_editor"
                ).format(function_name),
            }
            if issue["code"] in self.exclude_migration_tests:
                ignored.append(issue)
            else:
                warning.append(issue)

        # Detect wrong model imports
        # Forward
        issues = self.get_runpython_model_import_issues(runpython.code)
        for issue in issues:
            if issue["code"] in self.exclude_migration_tests:
                ignored.append(issue)
            else:
                error.append(issue)

        # Backward
        if runpython.reversible:
            issues = self.get_runpython_model_import_issues(runpython.reverse_code)
            for issue in issues:
                if issue and issue["code"] in self.exclude_migration_tests:
                    ignored.append(issue)
                else:
                    error.append(issue)

        # Detect warning if model variable name is not the same as model class
        issues = self.get_runpython_model_variable_naming_issues(runpython.code)
        for issue in issues:
            if issue and issue["code"] in self.exclude_migration_tests:
                ignored.append(issue)
            else:
                warning.append(issue)

        if runpython.reversible:
            issues = self.get_runpython_model_variable_naming_issues(
                runpython.reverse_code
            )
            for issue in issues:
                if issue and issue["code"] in self.exclude_migration_tests:
                    ignored.append(issue)
                else:
                    warning.append(issue)

        return error, ignored, warning

    @staticmethod
    def get_runpython_model_import_issues(code):
        model_object_regex = re.compile(r"[^a-zA-Z]?([a-zA-Z0-9]+?)\.objects")

        function_name = code.__name__
        source_code = inspect.getsource(code)

        called_models = model_object_regex.findall(source_code)
        issues = []
        for model in called_models:
            has_get_model_call = (
                re.search(
                    r"{}.*= +\w+\.get_model\(".format(model),
                    source_code,
                )
                is not None
            )
            if not has_get_model_call:
                issues.append(
                    {
                        "code": "RUNPYTHON_MODEL_IMPORT",
                        "msg": (
                            "'{}': Could not find an 'apps.get_model(\"...\", \"{}\")' "
                            "call. Importing the model directly is incorrect for "
                            "data migrations."
                        ).format(function_name, model),
                    }
                )
        return issues

    @staticmethod
    def get_runpython_model_variable_naming_issues(code):
        model_object_regex = re.compile(r"[^a-zA-Z]?([a-zA-Z0-9]+?)\.objects")

        function_name = code.__name__
        source_code = inspect.getsource(code)

        called_models = model_object_regex.findall(source_code)
        issues = []
        for model in called_models:
            has_same_model_name = (
                re.search(
                    r"{model}.*= +\w+?\.get_model\([^)]+?\.{model}.*?\)".format(
                        model=model
                    ),
                    source_code,
                    re.MULTILINE | re.DOTALL,
                )
                is not None
                or re.search(
                    r"{model}.*= +\w+?\.get_model\([^)]+?,[^)]*?{model}.*?\)".format(
                        model=model
                    ),
                    source_code,
                    re.MULTILINE | re.DOTALL,
                )
                is not None
            )
            if not has_same_model_name:
                issues.append(
                    {
                        "code": "RUNPYTHON_MODEL_VARIABLE_NAME",
                        "msg": (
                            "'{}': Model variable name {} is different from the "
                            "model class name that was found in the "
                            "apps.get_model(...) call."
                        ).format(function_name, model),
                    }
                )
        return issues

    def lint_runsql(self, runsql):
        error = []
        ignored = []
        warning = []

        # Detect warning on missing reverse operation
        if not runsql.reversible:
            issue = {
                "code": "RUNSQL_REVERSIBLE",
                "msg": "RunSQL data migration is not reversible",
            }
            if issue["code"] in self.exclude_migration_tests:
                ignored.append(issue)
            else:
                warning.append(issue)

        # Put the SQL in our SQL analyser
        if runsql.sql != RunSQL.noop:
            sql_statements = []
            if isinstance(runsql.sql, (list, tuple)):
                for sql in runsql.sql:
                    params = None
                    if isinstance(sql, (list, tuple)):
                        elements = len(sql)
                        if elements == 2:
                            sql, params = sql
                        else:
                            raise ValueError("Expected a 2-tuple but got %d" % elements)
                        sql_statements.append(sql % params)
                    else:
                        sql_statements.append(sql)
            else:
                sql_statements.append(runsql.sql)

            sql_errors, sql_ignored, sql_warnings = analyse_sql_statements(
                self.sql_analyser_class,
                sql_statements,
                self.exclude_migration_tests,
            )
            if sql_errors:
                error += sql_errors
            if sql_ignored:
                ignored += sql_ignored
            if sql_warnings:
                warning += sql_warnings

        # And analysse the reverse SQL
        if runsql.reversible and runsql.reverse_sql != RunSQL.noop:
            sql_statements = []
            if isinstance(runsql.reverse_sql, (list, tuple)):
                for sql in runsql.reverse_sql:
                    params = None
                    if isinstance(sql, (list, tuple)):
                        elements = len(sql)
                        if elements == 2:
                            sql, params = sql
                        else:
                            raise ValueError("Expected a 2-tuple but got %d" % elements)
                        sql_statements.append(sql % params)
                    else:
                        sql_statements.append(sql)
            else:
                sql_statements.append(runsql.reverse_sql)

            sql_errors, sql_ignored, sql_warnings = analyse_sql_statements(
                self.sql_analyser_class,
                sql_statements,
                self.exclude_migration_tests,
            )
            if sql_errors:
                error += sql_errors
            if sql_ignored:
                ignored += sql_ignored
            if sql_warnings:
                warning += sql_warnings

        return error, ignored, warning
