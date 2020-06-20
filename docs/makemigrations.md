# makemigrations

The linter can override behaviour of the [Django makemigrations command](https://docs.djangoproject.com/en/dev/ref/django-admin/#django-admin-makemigrations).

Either:
 * by specifying the `--lint` option in the command line
 * by setting the `MIGRATION_LINTER_OVERRIDE_MAKEMIGRATIONS` Django setting to `True`

## Example
```
$ python manage.py makemigrations --lint

Migrations for 'app_correct':
  tests/test_project/app_correct/migrations/0003_a_column.py
    - Add field column to a
Linting for 'app_correct':
(app_correct, 0003_a_column)... ERR
        NOT NULL constraint on columns
Deleted tests/test_project/app_correct/migrations/0003_a_column.py
```

## Options

Among the options that can be given, additionally to the default `makemigrations` options, you can count the options
to configure what should be linted:
* `--database DATABASE` - specify the database for which to generate the SQL. Defaults to *default*.
* `--warnings-as-errors` - handle warnings as errors and therefore return an error status code if we should.
* `--exclude-migration-tests MIGRATION_TEST_CODE [...]` - specify backward incompatible migration tests to be ignored using the code (e.g. ALTER_COLUMN).
