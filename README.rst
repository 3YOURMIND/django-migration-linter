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

``django-migration-linter DJANGO_PROJECT_FOLDER [GIT_COMMIT_ID] [--ignore-name-contains=IGNORE_NAME_CONTAINS] [--include-apps INCLUDE_APPS [INCLUDE_APPS ...] | --exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]]``

================================================== ===========================================================================================================================
                   Parameter                                                                            Description
================================================== ===========================================================================================================================
``DJANGO_PROJECT_FOLDER``                          An absolute or relative path to the django project.
``GIT_COMMIT_ID``                                  If specified, only migrations since this commit will be taken into account. If not specified, all migrations will be linted.
``--ignore-name-contains IGNORE_NAME_CONTAINS``    Ignore migrations containing this name.
``--ignore-name IGNORE_NAME [IGNORE_NAME ...]``    Ignore migrations with exactly one of these names.
``--include-apps INCLUDE_APPS [INCLUDE_APPS ...]`` Check only migrations that are in the specified django apps.
``--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]`` Ignore migrations that are in the specified django apps.
``--verbose or -v``                                Print more information during execution.
``--database DATABASE``                            Specify the database for which to generate the SQL. Defaults to *default*.
``--cache-path PATH``                              specify a directory that should be used to store cache-files in.
``--no-cache``                                     Don't use a cache.
================================================== ===========================================================================================================================

Examples
--------

3YOURMIND is running the linter on every build getting pushed through CI.
Checkout the ``examples/`` folder to see how you could integrate the linter in your test suite.

Backward incompatible migrations
--------------------------------

The linter analyses your migrations and checks the SQL for:

- Added ``NOT NULL`` columns, which don't have a DEFAULT value
- Dropping columns
- Renaming columns
- Renaming tables
- Altering columns (which can be backward compatible and eventually ignored)

Those are the most important and frequent backward incompatible migrations. We are happy to add more if you have some.

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

Cache
-----
By default, the linter uses a cache to prevent linting the same migration again.
The default location of the cache on Linux is
``/home/<username>/.cache/django-migration-linter/<version>/<ldjango-project>.pickle``.

Since the linter uses hashes, modifying migration files, will re-run the linter on that migration.
If you want to run the linter without cache, use the flag ``--no-cache``.
If you want to invalidate the cache, delete the cache folder.

Tests
-----

The easiest way to run the tests is to invoke `tox`_.

Contributing
------------

First, thank you very much if you want to contribute to the project.
Please base your work on the ``master`` branch and also target this branch in your pull request.

Blog post
---------

`Keeping Django database migrations backward compatible`_

License
-------

*django-migration-linter* is released under the `Apache 2.0 License`_.


.. _`tox`: https://pypi.python.org/pypi/tox
.. _`Keeping Django database migrations backward compatible`: https://medium.com/3yourmind/keeping-django-database-migrations-backward-compatible-727820260dbb
.. _`Apache 2.0 License`: https://github.com/3YOURMIND/django-migration-linter/blob/master/LICENSE
