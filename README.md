# Django migration linter

Detect backward incompatible migrations for your django project. All in one file.

## Usage

`python migration_linter.py DJANGO_PROJECT_FOLDER [GIT_COMMIT_ID] [--ignore-name-contains=IGNORE_NAME_CONTAINS] [--include-apps INCLUDE_APPS [INCLUDE_APPS ...] | --exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]]`

* `DJANGO_PROJECT_FOLDER` - an absolute or relative path to the django project.
* `GIT_COMMIT_ID` - if specified, only migrations since this commit will be taken into account. If not specified, the initial repo commit will be used.
* `--ignore-name-contains IGNORE_NAME_CONTAINS`- ignore migrations containing this name
* `--include-apps INCLUDE_APPS [INCLUDE_APPS ...]` - check only migrations that are in the specified django apps
* `--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]` - ignore migrations that are in the specified django apps
* `--verbose` or `-v` - print more information during execution

## Requirements

Needed software (in PATH):

* `python` (only tested on python2.7 (yet))
* `git`
* UNIX command line tools like `tail`

The linter will try to detect whether if the project is a django project and is versioned with git.

## Tests

Launch the tests with: `python -m unittest test_migration_linter`

More test are to be written.

## Improvements

* Add an appropriate license
* More tests (always!)
* Detect data migration (not only scheme migrations)
* Detection dependent on specified database (mysql, postgresql, ...)
