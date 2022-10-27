import ast
import re
from os import path

from setuptools import find_packages, setup

PROJECT_DIR = path.abspath(path.dirname(__file__))


def get_version():
    constants = path.join(PROJECT_DIR, "django_migration_linter", "constants.py")
    _version_re = re.compile(r"__version__\s+=\s+(?P<version>.*)")
    with open(constants) as f:
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
    packages=find_packages(include=["django_migration_linter*"]),
    install_requires=[
        "django>=2.2",
        "appdirs>=1.4.3",
        "toml>=0.10.2",
    ],
    extras_require={
        "test": [
            "tox>=3.15.2",
            "mysqlclient>=1.4.6",
            "psycopg2>=2.8.5",
            "django_add_default_value>=0.4.0",
            "coverage>=5.5",
        ],
    },
    keywords="django migration lint linter database backward compatibility",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
