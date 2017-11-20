# Django migration linter

Detect backward incompatible migrations for your django project.

## Usage

`python migration_linter.py DJANGO_PROJECT_FOLDER [GIT_COMMIT_ID] [--ignore-name-contains=IGNORE_NAME_CONTAINS] [--include-apps INCLUDE_APPS [INCLUDE_APPS ...] | --exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]]`

* `DJANGO_PROJECT_FOLDER` - an absolute or relative path to the django project.
* `GIT_COMMIT_ID` - if specified, only migrations since this commit will be taken into account. If not specified, the initial repo commit will be used.
* `--ignore-name-contains IGNORE_NAME_CONTAINS` - ignore migrations containing this name
* `--ignore-name IGNORE_NAME [IGNORE_NAME ...]` - ignore migrations with exactly one of these names
* `--include-apps INCLUDE_APPS [INCLUDE_APPS ...]` - check only migrations that are in the specified django apps
* `--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]` - ignore migrations that are in the specified django apps
* `--verbose` or `-v` - print more information during execution
* `--database DATABASE` - specify the database for which to generate the SQL. Defaults to *default*

## Requirements

Needed software (in PATH):

* `python`
* `git`
* UNIX command line tools like `tail`

The linter will try to detect if the project is a django project and is versioned with git.

## Tests

The easiest way to run the tests is to invoke [py.test](https://docs.pytest.org/en/latest/).

More tests are always welcome.
