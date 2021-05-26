# Usage

## Command line usage

The linter is installed as a Django app and is integrated through the Django management command system. 

`python manage.py lintmigrations [app_label] [migration_name]`

The three main usages are:

* Lint your entire code base
`python manage.py lintmigrations`

* Lint one Django app
`python manage.py lintmigrations app_label`

* Lint a specific migration
`python manage.py lintmigrations app_label migration_name`

Below the detailed command line options, which can all also be defined using a config file (`setup.cfg`, `tox.ini`, `.django_migration_linter.cfg`):

|                   Parameter                                  |                                        Description                                                                          |
|--------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------|
|`--git-commit-id GIT_COMMIT_ID`                               | If specified, only migrations since this commit will be taken into account.                                                 |
|`--ignore-name-contains IGNORE_NAME_CONTAINS`                 | Ignore migrations containing this name.                                                                                     |
|`--ignore-name IGNORE_NAME [IGNORE_NAME ...]`                 | Ignore migrations with exactly one of these names.                                                                          |
|`--include-name-contains INCLUDE_NAME_CONTAINS`               | Include migrations containing this name.                                                                                    |
|`--include-name INCLUDE_NAME [INCLUDE_NAME ...]`              | Include migrations with exactly one of these names.                                                                         |
|`--include-apps INCLUDE_APPS [INCLUDE_APPS ...]`              | Check only migrations that are in the specified django apps.                                                                |
|`--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]`              | Ignore migrations that are in the specified django apps.                                                                    |
|`--exclude-migration-tests MIGRATION_TEST_CODE [...]`         | Specify backward incompatible migration tests to be ignored using the code (e.g. ALTER_COLUMN).                             |
|`--verbosity or -v {0,1,2,3}`                                 | Print more information during execution.                                                                                    |
|`--database DATABASE`                                         | Specify the database for which to generate the SQL. Defaults to *default*.                                                  |
|`--cache-path PATH`                                           | specify a directory that should be used to store cache-files in.                                                            |
|`--no-cache`                                                  | Don't use a cache.                                                                                                          |
|`--applied-migrations`                                        | Only lint migrations that are applied to the selected database. Other migrations are ignored.                               |
|`--unapplied-migrations`                                      | Only lint migrations that are not yet applied to the selected database. Other migrations are ignored.                       |
|`--project-root-path DJANGO_PROJECT_FOLDER`                   | An absolute or relative path to the django project.                                                                         |
|`--include-migrations-from FILE_PATH`                         | If specified, only migrations listed in the given file will be considered.                                                  |
|`--quiet or -q {ok,ignore,warning,error}`                     | Suppress certain output messages, instead of writing them to stdout.                                                        |
|`--warnings-as-errors`                                        | Handle warnings as errors and therefore return an error status code if we should.                                           |

## File configuration

Example `setup.cfg` file:

```
[django_migration_linter]
no_cache = True
exclude_apps = users
```

## Ignoring migrations

You can also ignore migrations by adding an `IgnoreMigration()` to your migration operations:
```
from django.db import migrations, models
import django_migration_linter as linter

class Migration(migrations.Migration):
    dependencies = [...]
    operations = [
        linter.IgnoreMigration(),
        # ...
    ]
```

Or you can restrict the migrations that should be selected by a file containing there paths with the `--include-migrations-from` option.

## Ignoring migration tests

You can also ignore backward incompatible migration tests by adding this option during execution:

`python manage.py lintmigrations --exclude-migration-tests ALTER_COLUMN`

The migration test codes can be found in the [corresponding source code files](../django_migration_linter/sql_analyser/base.py).

## Production usage example

[3YOURMIND](https://www.3yourmind.com/) is running the linter on every build getting pushed through CI.
That enables to be sure that the migrations will allow A/B testing, Blue/Green deployment, and they won't break your development environment.
A non-zero error code is returned to express that at least one invalid migration has been found.
