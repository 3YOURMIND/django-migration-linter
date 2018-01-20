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

#
# You can use this file to integrate the migration-linter into your tests.
# In this example only the migrations after the latest version bump are
# considered.
#

import os
from subprocess import Popen, PIPE
from unittest import TestCase

from django.conf import settings


# Replace that function according to your needs
def read_version_file():
    with open('version', 'r') as f:
        return '{0}'.format(f.read().replace('\n', ''))


class MigrationTest(TestCase):
    ignored_migrations = (
    )
    excluded_apps = (
    )

    @classmethod
    def setUpClass(cls):
        super(MigrationTest, cls).setUpClass()
        cls.project_path = os.path.dirname(settings.PROJECT_PATH)
        cls.latest_tag = '{0}'.format(read_version_file())

    def test_latest_migrations(self):
        ignored_migration_parameter = '--ignore-name ' + \
                                      ' '.join(self.ignored_migrations) \
            if self.ignored_migrations else ''

        excluded_apps_parameter = '--exclude-apps ' + \
                                  ' '.join(self.excluded_apps) \
            if self.excluded_apps else ''

        linter_cmd = 'django-migration-linter {0} {1} {2} {3}'.format(
            self.project_path,
            self.latest_tag,
            ignored_migration_parameter,
            excluded_apps_parameter)

        lint_process = Popen(linter_cmd, shell=True, stdout=PIPE, stderr=PIPE)
        lint_process.wait()

        if lint_process.returncode != 0:
            out, err = lint_process.communicate()
            out = out.decode('ascii')
            self.fail('The migration linter found errors\n'
                      'migration command: {0}\n'
                      'STDOUT: {1}\n'
                      'STDERR: {2}\n'.
                      format(linter_cmd, out, err)
                      )
