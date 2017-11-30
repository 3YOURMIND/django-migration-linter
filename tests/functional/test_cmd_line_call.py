import unittest
from subprocess import Popen, PIPE
from django_migration_linter import utils
from tests import fixtures


class CallLinterFromCommandLineTest(unittest.TestCase):
    def test_call_linter_cmd_line_working(self):
        cmd = 'django-migration-linter {0}'.format(fixtures.CORRECT_PROJECT)

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
        cmd = 'django-migration-linter {0}'.format(
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
        cmd = 'django-migration-linter {0} --exclude-apps test_app2'.format(
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
        cmd = 'django-migration-linter {0} --include-apps test_app2'.format(
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
        cmd = 'django-migration-linter {0} --ignore-name 0001_initial'.format(
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
        cmd = 'django-migration-linter {0} --ignore-name-contains 0001'.format(
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
        cmd = 'django-migration-linter {0} d7125d5f4f0cc9623f670a66c54f131acc50032d'.format(
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
