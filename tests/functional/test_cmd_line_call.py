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

import unittest
from subprocess import Popen, PIPE
from django_migration_linter import utils
from tests import fixtures
import sys


class CallLinterFromCommandLineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(CallLinterFromCommandLineTest, cls).setUpClass()
        linter_name = 'django-migration-linter'
        cls.linter_exec = '{0}/bin/{1}'.format(sys.prefix,  linter_name) if hasattr(sys, 'real_prefix') else linter_name

    def test_call_linter_cmd_line_working(self):
        cmd = '{0} {1}'.format(self.linter_exec, fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].endswith('OK'))
        self.assertTrue(lines[2].endswith('OK'))

    def test_call_linter_cmd_line_errors(self):
        cmd = '{0} {1}'.format(
            self.linter_exec,
            fixtures.ADD_NOT_NULL_COLUMN_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertNotEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        print(lines)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].endswith('ERR'))
        self.assertTrue('RENAMING tables' in lines[2])

    def test_call_linter_cmd_line_exclude_apps(self):
        cmd = '{0} {1} --exclude-apps test_app2'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('OK'))
        self.assertTrue(lines[1].endswith('OK'))
        self.assertTrue(lines[2].endswith('IGNORE'))

    def test_call_linter_cmd_line_include_apps(self):
        cmd = '{0} {1} --include-apps test_app2'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('IGNORE'))
        self.assertTrue(lines[1].endswith('IGNORE'))
        self.assertTrue(lines[2].endswith('OK'))

    def test_call_linter_cmd_line_ignore_name(self):
        cmd = '{0} {1} --ignore-name 0001_initial'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('IGNORE'))
        self.assertTrue(lines[1].endswith('OK'))
        self.assertTrue(lines[2].endswith('OK'))

    def test_call_linter_cmd_line_ignore_name_contains(self):
        cmd = '{0} {1} --ignore-name-contains 0001'.format(
            self.linter_exec,
            fixtures.CORRECT_PROJECT)

        process = Popen(
            cmd, shell=True, stdout=PIPE, stderr=PIPE)
        process.wait()
        self.assertEqual(process.returncode, 0)
        lines = list(map(utils.clean_bytes_to_str, process.stdout.readlines()))
        self.assertEqual(len(lines), 5)
        self.assertTrue(lines[0].endswith('IGNORE'))
        self.assertTrue(lines[1].endswith('OK'))
        self.assertTrue(lines[2].endswith('IGNORE'))

    def test_call_linter_cmd_line_git_id(self):
        cmd = '{0} {1} d7125d5f4f0cc9623f670a66c54f131acc50032d'.format(
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
        cmd = '{0} {1} 154ecf6119325cc3b1f3f5a4e709bfbd61a4a4ba'.format(
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
