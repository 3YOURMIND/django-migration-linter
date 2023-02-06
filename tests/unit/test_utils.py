from __future__ import annotations

import unittest

from django_migration_linter.utils import split_migration_path, split_path, split_migration_prefix


class SplitPathTestCase(unittest.TestCase):
    def test_split_path(self):
        split = split_path("foo/bar/fuz.py")
        self.assertEqual(split, ["foo", "bar", "fuz.py"])

    def test_split_full_path(self):
        split = split_path("/foo/bar/fuz.py")
        self.assertEqual(split, ["/", "foo", "bar", "fuz.py"])

    def test_split_folder_path(self):
        split = split_path("/foo/bar")
        self.assertEqual(split, ["/", "foo", "bar"])

    def test_split_folder_path_trailing_slash(self):
        split = split_path("/foo/bar/")
        self.assertEqual(split, ["/", "foo", "bar"])

    def test_split_folder_path_trailing_slashes(self):
        split = split_path("/foo/bar///")
        self.assertEqual(split, ["/", "foo", "bar"])

    def test_split_migration_long_path(self):
        input_path = "apps/the_app/migrations/0001_stuff.py"
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, "the_app")
        self.assertEqual(mig, "0001_stuff")

    def test_split_migration_path(self):
        input_path = "the_app/migrations/0001_stuff.py"
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, "the_app")
        self.assertEqual(mig, "0001_stuff")

    def test_split_migration_full_path(self):
        input_path = "/home/user/djangostuff/apps/the_app/migrations/0001_stuff.py"
        app, mig = split_migration_path(input_path)
        self.assertEqual(app, "the_app")
        self.assertEqual(mig, "0001_stuff")

    def test_split_migration_long_prefix(self):
        input_path = "apps/the_app/migrations/0001_stuff.py"
        prefix, mig = split_migration_prefix(input_path)
        self.assertEqual(prefix, "apps/the_app")
        self.assertEqual(mig, "0001_stuff")

    def test_split_migration_prefix(self):
        input_path = "the_app/migrations/0001_stuff.py"
        prefix, mig = split_migration_prefix(input_path)
        self.assertEqual(prefix, "the_app")
        self.assertEqual(mig, "0001_stuff")

    def test_split_migration_full_prefix(self):
        input_path = "/home/user/djangostuff/apps/the_app/migrations/0001_stuff.py"
        prefix, mig = split_migration_prefix(input_path)
        self.assertEqual(prefix, "/home/user/djangostuff/apps/the_app")
        self.assertEqual(mig, "0001_stuff")
