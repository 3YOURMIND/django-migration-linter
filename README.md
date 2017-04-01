# Django migration checker

Detect backward incompatible migrations for your django projects. All in one file.

## Usage

`python migration_checker.py DJANGO_PROJECT_FOLDER [GIT_COMMIT_ID]`

* `DJANGO_PROJECT_FOLDER` - an absolute or relative path to the django project.
* `GIT_COMMIT_ID` - if specified, only migrations since this commit will be taken into account. If not specified, the initial repo commit will be used.

## Requirements

Needed software (in PATH):

* `python` (only tested on python2.7 (yet))
* `git`
* UNIX command line tools like `tail`

The checker will try to detect whether if the project is a django project and is versioned with git.

## Tests

Launch the tests with: `python -m unittest test_migration_checker`

More test are to be written.

## Improvements

* More tests (always!)
* Possibility to ignore certain migrations
* Possibility to only check certain apps within the project (and/or exclude certain ones)
* Detect data migration (not only scheme migrations)
* Detection dependent on specified database (mysql, postgresql, ...)

## Credits

[3YOURMIND GmbH](https://www.3yourmind.com)
