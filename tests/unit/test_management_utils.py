import os
from unittest.mock import patch

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

    def test_read_config_file_dn_exist(self):
        """
        Check no errors are raised if the .cfg file does not exist.
        """
        cfg_options = utils.read_config_file(EXAMPLE_OPTIONS)
        expected = {}
        self.assertDictEqual(cfg_options, expected)

    # @override_settings(
    #     MIGRATION_LINTER_OPTIONS={"interactive": False, "name": "test_name"}
    # )
    # def test_read_django_settings_exist(self):
    #     django_options = utils.read_django_settings(EXAMPLE_OPTIONS)
    #     expected = {"interactive": False, "name": "test_name"}
    #     self.assertDictEqual(django_options, expected)

    def test_read_django_settings_dn_exist(self):
        """
        Check no errors are raised if the settings key does not exist.
        """
        django_options = utils.read_django_settings(EXAMPLE_OPTIONS)
        expected = {}
        self.assertDictEqual(django_options, expected)

    def test_load_config_priority(self):
        """ """

        options = utils.load_config(EXAMPLE_OPTIONS)
