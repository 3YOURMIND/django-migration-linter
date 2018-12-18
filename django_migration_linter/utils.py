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

from __future__ import print_function
import os
import sys

from django_migration_linter.constants import DEFAULT_CACHE_PATH


def is_django_project(path):
    django_manage_file = os.path.join(path, 'manage.py')
    return os.path.isfile(django_manage_file)


def is_git_project(path):
    git_directory = os.path.join(path, '.git')
    return os.path.isdir(git_directory)


def is_directory(path):
    return os.path.isdir(path)


def print_stderr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def find_project_settings_module(path):
    """Explore path recursively to the first settings.py file
    and translate the name to package notation 'mysite.settings'
    """
    for root, dirs, files in os.walk(path):
        for file_name in files:
            if file_name == 'settings.py':
                return os.path.join(
                    root.replace(path, ''),
                    file_name).replace('/', '.').rstrip('.py')


def split_path(path):
    a, b = os.path.split(path)
    return (split_path(a) if (len(a) > 0 and a != '/') else []) + [b]


def clean_bytes_to_str(byte_input):
    return byte_input.decode('utf-8').strip()


def get_default_cache_file(project_name):
    return os.path.join(DEFAULT_CACHE_PATH, '{0}.pickle'.format(project_name))
