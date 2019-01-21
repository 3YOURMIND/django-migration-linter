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

import os
import shutil
import unittest
from subprocess import Popen, PIPE
from django_migration_linter import utils, DEFAULT_CACHE_PATH, constants
from tests import fixtures
import sys


class CallLinterFromCommandLineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(CallLinterFromCommandLineTest, cls).setUpClass()
        linter_name = 'django-migration-linter'
        cls.linter_exec = '{0}/bin/{1}'.format(sys.prefix,  linter_name) if hasattr(sys, 'real_prefix') else linter_name

    def test_call_linter_cmd_line_working(self):
        cmd = '{0} --no-cache {1}'.format(self.linter_exec, fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... OK",
                 "(test_app1, 0002_a_new_null_field)... OK",
                 "(test_app2, 0001_foo)... OK",
                 "(test_app3, 0001_initial)... OK",
             ])
        )

    def test_call_linter_cmd_line_errors(self):
        cmd = '{0} --no-cache {1}'.format(
            self.linter_exec,
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertNotEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].endswith('ERR'))
        self.assertTrue('RENAMING tables' in lines[2])

    def test_call_linter_cmd_line_exclude_apps(self):
        cmd = '{0} --no-cache {1} --exclude-apps test_app2'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... OK",
                 "(test_app1, 0002_a_new_null_field)... OK",
                 "(test_app2, 0001_foo)... IGNORE",
                 "(test_app3, 0001_initial)... OK",
             ])
        )

    def test_call_linter_cmd_line_include_apps(self):
        cmd = '{0} --no-cache {1} --include-apps test_app2'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... IGNORE",
                 "(test_app1, 0002_a_new_null_field)... IGNORE",
                 "(test_app2, 0001_foo)... OK",
                 "(test_app3, 0001_initial)... IGNORE",
             ])
        )

    def test_call_linter_cmd_line_ignore_name(self):
        cmd = '{0} --no-cache {1} --ignore-name 0001_initial'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... IGNORE",
                 "(test_app1, 0002_a_new_null_field)... OK",
                 "(test_app2, 0001_foo)... OK",
                 "(test_app3, 0001_initial)... IGNORE",
             ])
        )

    def test_call_linter_cmd_line_ignore_name_contains(self):
        cmd = '{0} --no-cache {1} --ignore-name-contains 0001'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... IGNORE",
                 "(test_app1, 0002_a_new_null_field)... OK",
                 "(test_app2, 0001_foo)... IGNORE",
                 "(test_app3, 0001_initial)... IGNORE",
             ])
        )

    def test_call_linter_cmd_line_cache(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_correct_project.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)
        cmd = '{0} {1}'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT
        )

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertTrue(os.path.exists(DEFAULT_CACHE_PATH))

    def test_call_linter_cmd_line_cache_path(self):
        if os.path.exists('/tmp/migration-linter-cache-tests/'):
            shutil.rmtree('/tmp/migration-linter-cache-tests/')
        cmd = '{0} {1} --cache-path={2}'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT,
            '/tmp/migration-linter-cache-tests/'
        )

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        self.assertTrue(os.path.exists('/tmp/migration-linter-cache-tests'))

    def test_call_linter_cmd_line_no_cache(self):
        cache_file = os.path.join(DEFAULT_CACHE_PATH, 'test_correct_project.pickle')
        if os.path.exists(cache_file):
            os.remove(cache_file)

        cmd = '{0} --no-cache {1}'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT
        )

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        self.assertFalse(os.path.exists(cache_file))

    def test_call_linter_cmd_line_git_id(self):
        cmd = '{0} --no-cache {1} d7125d5f4f0cc9623f670a66c54f131acc50032d'.format(
            self.linter_exec,
            fixtures.MULTI_COMMIT_PROJECT)
        fixtures.prepare_git_project(fixtures.MULTI_COMMIT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].startswith('*** Summary'))

    def test_call_linter_with_deleted_migrations(self):
        cmd = '{0} --no-cache {1} 154ecf6119325cc3b1f3f5a4e709bfbd61a4a4ba'.format(
            self.linter_exec,
            fixtures.DELETED_MIGRATION_PROJECT)
        fixtures.prepare_git_project(fixtures.DELETED_MIGRATION_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].startswith('*** Summary'))

    def test_call_from_within_project(self):
        cmd = 'cd {0} && {1} --no-cache .'.format(
            fixtures.CORRECT_PROJECT,
            self.linter_exec)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 6)
        self.assertEqual(
            sorted(lines[:4]),
            sorted([
                 "(test_app1, 0001_initial)... OK",
                 "(test_app1, 0002_a_new_null_field)... OK",
                 "(test_app2, 0001_foo)... OK",
                 "(test_app3, 0001_initial)... OK",
             ])
        )

    def test_call_project_non_git_root(self):
        # could use tag: version_ok (but doesn't work in Travis)
        cmd = '{0} --no-cache {1} 2c46f438a89972f9ce2d5151a825a5bfb7f7db4b'.format(
            self.linter_exec,
            fixtures.NON_GIT_ROOT_DJANGO_PROJECT)
        fixtures.prepare_git_project(fixtures.NON_GIT_ROOT_GIT_FOLDER)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 3)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].startswith('*** Summary'))

    def test_call_project_non_git_root_ko(self):
        # could use tag: version_ko (but doesn't work in Travis)
        cmd = '{0} --no-cache {1} 0140e142724fc58944797f9ddc2ebf964146339a'.format(
            self.linter_exec,
            fixtures.NON_GIT_ROOT_DJANGO_PROJECT)
        fixtures.prepare_git_project(fixtures.NON_GIT_ROOT_GIT_FOLDER)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertNotEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('ERR'))
        self.assertTrue(lines[2].endswith('OK'))
        self.assertTrue(lines[3].startswith('*** Summary'))


class VersionOptionLinterFromCommandLineTest(CallLinterFromCommandLineTest):
    def test_call_with_version_option(self):
        cmd = "{} --version".format(self.linter_exec)
        process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        process_read_stream = process.stderr if sys.version_info.major == 2 else process.stdout
        lines = list(map(utils.clean_bytes_to_str, process_read_stream.readlines()))
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "django-migration-linter {}".format(constants.__version__))

    def test_call_with_short_version_option(self):
        cmd = "{} -V".format(self.linter_exec)
        process = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        process_read_stream = process.stderr if sys.version_info.major == 2 else process.stdout
        lines = list(map(utils.clean_bytes_to_str, process_read_stream.readlines()))
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "django-migration-linter {}".format(constants.__version__))
