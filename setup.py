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

from codecs import open
from os import path
from setuptools import setup, find_packages


PROJECT_DIR = path.abspath(path.dirname(__file__))

with open(path.join(PROJECT_DIR, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

install_requirements = [
]

test_requirements = [
    'tox',
    'pytest',
    'django>=1.9',
    'django-fake-database-backends',
    'flake8'
]

setup(
    name='django-migration-linter',
    version='0.0.3',

    description='Detect backward incompatible migrations for your django project',
    long_description=long_description,
    url='https://github.com/3YOURMIND/django-migration-linter',
    author='3YOURMIND GmbH',
    license='Apache License 2.0',

    packages=find_packages(exclude=['tests/']),
    install_requires=install_requirements,
    extras_require={
        'test': test_requirements
    },
    entry_points={
        'console_scripts': [
            'django-migration-linter = django_migration_linter.migration_linter:_main'
        ]
    },

    keywords='django migration lint linter database backward compatibility',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',

        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
