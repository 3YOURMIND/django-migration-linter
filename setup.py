import ast
import re
from os import path
from setuptools import setup, find_packages


PROJECT_DIR = path.abspath(path.dirname(__file__))


def get_version():
    constants = path.join(PROJECT_DIR, "django_migration_linter", "constants.py")
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(constants, "r") as f:
        match = _version_re.search(f.read())
        version = match.group("version") if match is not None else '"unknown"'
    return str(ast.literal_eval(version))


with open(path.join(PROJECT_DIR, "README.md")) as f:
    long_description = f.read()


setup(
    name="django-migration-linter",
    version=get_version(),
    description="Detect backward incompatible migrations for your django project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/3YOURMIND/django-migration-linter",
    author="3YOURMIND GmbH",
    author_email="david.wobrock@gmail.com",
    license="Apache License 2.0",
    packages=find_packages(exclude=["tests/"]),
    install_requires=[
        "django>=1.11",
        "appdirs>=1.4.3",
        'enum34>=1.1.6;python_version<"3.4"',
        "six>=1.14.0",
    ],
    extras_require={
        "test": [
            "tox>=3.15.2",
            "mysqlclient>=1.4.6",
            "psycopg2-binary>=2.8.5",
            "django_add_default_value>=0.4.0",
            'mock>=3.0.5;python_version<"3.3"',
            'backports.tempfile>=1.0;python_version<="2.7"',
        ]
    },
    keywords="django migration lint linter database backward compatibility",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 1.11",
        "Framework :: Django :: 2.0",
        "Framework :: Django :: 2.1",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
