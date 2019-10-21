=======================
Django migration linter
=======================

Detect backward incompatible migrations for your django project. It will save you time by making sure migrations will not break anything.

.. image:: https://travis-ci.org/3YOURMIND/django-migration-linter.svg?branch=master
    :target: https://travis-ci.org/3YOURMIND/django-migration-linter

.. image:: https://img.shields.io/pypi/v/django-migration-linter.svg
    :target: https://pypi.python.org/pypi/django-migration-linter/

.. image:: https://img.shields.io/github/license/3yourmind/django-migration-linter.svg
    :target: ./LICENSE

.. image:: https://img.shields.io/badge/PR-welcome-green.svg
    :target: https://github.com/3YOURMIND/django-migration-linter/pulls

.. image:: https://img.shields.io/badge/3YOURMIND-Hiring-brightgreen.svg
    :target: https://www.3yourmind.com/career

.. image:: https://img.shields.io/github/stars/3YOURMIND/django-migration-linter.svg?style=social&label=Stars
    :target: https://github.com/3YOURMIND/django-migration-linter/stargazers

Installation
------------

``pip install django-migration-linter``


Usage
-----


Add the migration linter your ``INSTALLED_APPS``:

.. code-block::

    INSTALLED_APPS = [
        ...,
        "django_migration_linter",
        ...,
    ]


``python manage.py lintmigrations [GIT_COMMIT_ID] [--ignore-name-contains IGNORE_NAME_CONTAINS] [--include-apps INCLUDE_APPS [INCLUDE_APPS ...] | --exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]] [--exclude-migration-tests MIGRATION_TEST_CODE [MIGRATION_TEST_CODE ...]] [--project-root-path DJANGO_PROJECT_FOLDER] [--include-migrations-from FILE_PATH] [--quiet {ok,ignore,error} [{ok,ignore,error} ...]]``

================================================================ ===========================================================================================================================
                   Parameter                                                                            Description
================================================================ ===========================================================================================================================
``GIT_COMMIT_ID``                                                If specified, only migrations since this commit will be taken into account. If not specified, all migrations will be linted.
``--ignore-name-contains IGNORE_NAME_CONTAINS``                  Ignore migrations containing this name.
``--ignore-name IGNORE_NAME [IGNORE_NAME ...]``                  Ignore migrations with exactly one of these names.
``--include-apps INCLUDE_APPS [INCLUDE_APPS ...]``               Check only migrations that are in the specified django apps.
``--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]``               Ignore migrations that are in the specified django apps.
``--exclude-migration-tests MIGRATION_TEST_CODE [...]``          Specify backward incompatible migration tests to be ignored using the code (e.g. ALTER_COLUMN).
``--verbose or -v``                                              Print more information during execution.
``--database DATABASE``                                          Specify the database for which to generate the SQL. Defaults to *default*.
``--cache-path PATH``                                            specify a directory that should be used to store cache-files in.
``--no-cache``                                                   Don't use a cache.
``--applied-migrations``                                         Only lint migrations that are applied to the selected database. Other migrations are ignored.
``--unapplied-migrations``                                       Only lint migrations that are not yet applied to the selected database. Other migrations are ignored.
``--project-root-path DJANGO_PROJECT_FOLDER``                    An absolute or relative path to the django project.
``--include-migrations-from FILE_PATH``                          If specified, only migrations listed in the given file will be considered.
``--quiet or -q {ok,ignore,error}``                              Suppress certain output messages, instead of writing them to stdout.
================================================================ ===========================================================================================================================

Examples
--------

3YOURMIND is running the linter on every build getting pushed through CI.
That enables to be sure that the migrations will allow A/B testing, Blue/Green deployment and they won't break your development environment.
As every reasonable tool, a non-zero error code means that at least one invalid migration has been found.

Backward incompatible migrations
--------------------------------

The linter analyses your migrations and checks the SQL for:

- Added ``NOT NULL`` columns, which don't have a DEFAULT value
- Dropping columns
- Dropping tables
- Renaming columns
- Renaming tables
- Altering columns (which can be backward compatible and potentially ignored)
- Adding a unique constraint

Those are the most important and frequent backward incompatible migrations.
We are happy to add more if you can specify them to us.

Ignoring migrations
-------------------

You can also ignore migrations by adding this to your migrations:

.. code-block::

    import django_migration_linter as linter
    # ...

        operations = [
            linter.IgnoreMigration(),
            # ...
        ]
    # ...

Or you can restrict the migrations that should be selected by a file containing there paths with the ``--include-migrations-from`` option.

Ignoring migration tests
------------------------

You can also ignore backward incompatible migration tests by adding this option during execution:

``python manage.py lintmigrations --exclude-migration-tests ALTER_COLUMN``

The migration test codes can be found in the file ``django_migration_linter/sql_analyser.py``.

Cache
-----
By default, the linter uses a cache to prevent linting the same migration multiple times.
The default location of the cache on Linux is
``/home/<username>/.cache/django-migration-linter/<version>/<ldjango-project>_<database_name>.pickle``.

Since the linter uses hashes of the file's content, modifying a migration file will re-run the linter on that migration.
If you want to run the linter without cache, use the flag ``--no-cache``.
If you want to invalidate the cache, delete the cache folder.
The cache folder can also be defined manually through the ``--cache-path`` option.

Tests
-----

The easiest way to run the tests is to invoke `tox`_.

You will need to install the test requirements, which can be found in the ``setup.py`` file.
A good way to get started is to install the development version of the linter by doing ``pip install -e .[test]``.

To be able to fully test the linter, you will need both MySQL and PostgreSQL databases running.
You can either tweak the ``tests/test_project/settings.py`` file to get your DB settings right, or to have databases and users corresponding to the default Travis users.

Contributing
------------

First, thank you very much if you want to contribute to the project.
Please base your work on the ``master`` branch and also target this branch in your pull request.

Publishing the package
----------------------

A small note on how the linter is usually published to PyPi:

- ``python setup.py check --restructuredtext``
- ``python3 setup.py sdist bdist_wheel --universal``
- ``twine upload dist/django_migration_linter-X.Y.Z-py2.py3-none-any.whl dist/django-migration-linter-X.Y.Z.tar.gz``

Blog post
---------

`Keeping Django database migrations backward compatible`_

License
-------

*django-migration-linter* is released under the `Apache 2.0 License`_.


.. _`tox`: https://pypi.python.org/pypi/tox
.. _`Keeping Django database migrations backward compatible`: https://medium.com/3yourmind/keeping-django-database-migrations-backward-compatible-727820260dbb
.. _`Apache 2.0 License`: https://github.com/3YOURMIND/django-migration-linter/blob/master/LICENSE
