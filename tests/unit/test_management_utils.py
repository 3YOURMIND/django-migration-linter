import os
from unittest.mock import patch
import argparse

import unittest
from django.test import TestCase
from django.test.utils import override_settings

from django_migration_linter.management import utils


EXAMPLE_OPTIONS = {
    "verbosity": 1,
    "settings": None,
    "pythonpath": None,
    "traceback": False,
    "no_color": False,
    "force_color": False,
    "skip_checks": False,
    "dry_run": False,
    "merge": False,
    "empty": False,
    "interactive": True,
    "name": None,
    "include_header": True,
    "check_changes": False,
    "scriptable": False,
    "update": False,
    "lint": False,
    "database": None,
    "exclude_migration_tests": None,
    "warnings_as_errors": None,
    "sql_analyser": None,
}


def get_test_path(filename: str) -> str:
    """
    Returns path to test files
    """
    return os.path.join(os.path.dirname(__file__), f"files/{filename}")


class LoadConfigTestCase(unittest.TestCase):
    @patch(
        "django_migration_linter.management.utils.PYPROJECT_TOML",
        get_test_path("test_config.toml"),
    )
    def test_read_toml_file_exists(self):
        """
        Check we can read config options from a toml file.
        """
        toml_options = utils.read_toml_file(EXAMPLE_OPTIONS)
        expected = {"sql_analyser": "postgresql"}
        self.assertDictEqual(toml_options, expected)
    
    @patch(
        "django_migration_linter.management.utils.PYPROJECT_TOML",
        get_test_path("test_config.toml"),
    )
    def test_read_toml_file_drops_extras(self):
        """
        Check extra items listed in the toml file are dropped
        """
        toml_options = utils.read_toml_file(EXAMPLE_OPTIONS)
        expected = {"sql_analyser": "postgresql"}
        self.assertDictEqual(toml_options, expected)

    def test_read_toml_file_dn_exist(self):
        """
        Check no errors are raised if the toml file does not exist.
        """
        toml_options = utils.read_toml_file(EXAMPLE_OPTIONS)
        expected = {}
        self.assertDictEqual(toml_options, expected)

    @patch(
        "django_migration_linter.management.utils.DEFAULT_CONFIG_FILES",
        get_test_path("test_setup.cfg"),
    )
    def test_read_config_file_exists(self):
        """
        Check we can read config options from a config file
        """
        cfg_options = utils.read_config_file(EXAMPLE_OPTIONS)
        expected = {"traceback": True}
        self.assertDictEqual(cfg_options, expected)
    
    @patch(
        "django_migration_linter.management.utils.DEFAULT_CONFIG_FILES",
        get_test_path("test_setup.cfg"),
    )
    def test_read_config_file_drop_extra(self):
        """
        Check we can read config options from a config file
        """
        cfg_options = utils.read_config_file(EXAMPLE_OPTIONS)
        expected = {"traceback": True}
        self.assertDictEqual(cfg_options, expected)

    def test_read_config_file_dn_exist(self):
        """
        Check no errors are raised if the .cfg file does not exist.
        """
        cfg_options = utils.read_config_file(EXAMPLE_OPTIONS)
        expected = {}
        self.assertDictEqual(cfg_options, expected)

    @override_settings(
        MIGRATION_LINTER_OPTIONS={"interactive": False, "name": "test_name"}
    )
    def test_read_django_settings_exist(self):
        django_options = utils.read_django_settings(EXAMPLE_OPTIONS)
        expected = {"interactive": False, "name": "test_name"}
        self.assertDictEqual(django_options, expected)

    @override_settings(
        MIGRATION_LINTER_OPTIONS={"interactive": False, "name": "test_name", "not_a_real_setting": True}
    )
    def test_read_django_settings_drop_extra(self):
        django_options = utils.read_django_settings(EXAMPLE_OPTIONS)
        expected = {"interactive": False, "name": "test_name"}
        self.assertDictEqual(django_options, expected)

    def test_read_django_settings_dn_exist(self):
        """
        Check no errors are raised if the settings key does not exist.
        """
        django_options = utils.read_django_settings(EXAMPLE_OPTIONS)
        expected = {}
        self.assertDictEqual(django_options, expected)

    @patch("django_migration_linter.management.utils.read_django_settings", lambda options: {"a": 2})
    @patch("django_migration_linter.management.utils.read_config_file", lambda options: {"b": "3"})
    @patch("django_migration_linter.management.utils.read_toml_file", lambda options: {"a": 1,"b": 2, "c": "4", "d": False})
    def test_load_config_priority(self):
        """
        Check that the loading priority is respected.

        Expecting:
        a is overridden by django settings
        b is overridden by cfg file
        c is loaded from toml and converted to int
        d is overridden command line
        """

        parser = argparse.ArgumentParser()
        parser.add_argument("--a", default=1)
        parser.add_argument("--b", type=int, default=1)
        parser.add_argument("--c", type=int, default=1)
        parser.add_argument("--d", action="store_true")

        with patch('argparse._sys.argv', ["script.py"]):
            utils.set_defaults_from_conf(parser)

        expected = {
            "a": 2,
            "b": 3,
            "c": 4,
            "d": True
        }

        options = vars(parser.parse_args(["--d"]))

        self.assertDictEqual(options, expected)
