# Django migration linter

Detect backward incompatible migrations for your Django project.
It will save you time by making sure migrations will not break with a older codebase.

[![Travis](https://travis-ci.org/3YOURMIND/django-migration-linter.svg?branch=master)](https://travis-ci.org/3YOURMIND/django-migration-linter)
[![PyPI](https://img.shields.io/pypi/v/django-migration-linter.svg)](https://pypi.python.org/pypi/django-migration-linter/)
[![PR_Welcome](https://img.shields.io/badge/PR-welcome-green.svg)](https://github.com/3YOURMIND/django-migration-linter/pulls)
[![3YD_Hiring](https://img.shields.io/badge/3YOURMIND-Hiring-brightgreen.svg)](https://www.3yourmind.com/career)
[![GitHub_Stars](https://img.shields.io/github/stars/3YOURMIND/django-migration-linter.svg?style=social&label=Stars)](https://github.com/3YOURMIND/django-migration-linter/stargazers)

## Quick installation

```
pip install django-migration-linter
```

And add the migration linter your ``INSTALLED_APPS``:
```
    INSTALLED_APPS = [
        ...,
        "django_migration_linter",
        ...,
    ]
```

## Usage example

```
$ python manage.py lintmigrations

(app_add_not_null_column, 0001_create_table)... OK
(app_add_not_null_column, 0002_add_new_not_null_field)... ERR
        NOT NULL constraint on columns
(app_drop_table, 0001_initial)... OK
(app_drop_table, 0002_delete_a)... ERR
        DROPPING table
(app_ignore_migration, 0001_initial)... OK
(app_ignore_migration, 0002_ignore_migration)... IGNORE
(app_rename_table, 0001_initial)... OK
(app_rename_table, 0002_auto_20190414_1500)... ERR
        RENAMING tables

*** Summary ***
Valid migrations: 4/8
Erroneous migrations: 3/8
Migrations with warnings: 0/8
Ignored migrations: 1/8
```

The linter analysed all migrations from the Django project.
It found 3 migrations that are doing backward incompatible operations and 1 that is explicitly ignored.
The list of incompatibilities that the linter analyses [can be found at docs/incompatibilities.md](./docs/incompatibilities.md).

More advanced usages of the linter and options [can be found at docs/usage.md](./docs/usage.md).

### More information

Please find more documentation generally [in the docs/ folder](./docs/).

Some implementation details [can found in the ./docs/internals/ folder](./docs/internals/).

### Blog post

[Keeping Django database migrations backward compatible](https://medium.com/3yourmind/keeping-django-database-migrations-backward-compatible-727820260dbb)

### License

*django-migration-linter* is released under the [Apache 2.0 License](./LICENSE).

##### Maintained by [David Wobrock](https://github.com/David-Wobrock)
