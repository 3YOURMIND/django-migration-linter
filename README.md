# Django migration linter

> Detect backward incompatible migrations for your django project. It will save you time by making sure migrations will not break anything.

<a href="https://travis-ci.org/3YOURMIND/django-migration-linter"><img src="https://travis-ci.org/3YOURMIND/django-migration-linter.svg?branch=master" alt="badge of travis CI" /></a>
<a href="https://pypi.python.org/pypi/django-migration-linter/"><img src="https://img.shields.io/pypi/v/django-migration-linter.svg" alt="PyPi version" /></a>
<a href="./LICENSE"><img src="https://img.shields.io/github/license/3yourmind/django-migration-linter.svg" alt="badge of license" /></a>
<a href="https://github.com/3YOURMIND/django-migration-linter/pulls"><img src="https://img.shields.io/badge/PR-welcome-green.svg" alt="badge of pull request welcome" /></a>
<a href="https://www.3yourmind.com/career"><img src="https://img.shields.io/badge/3YOURMIND-Hiring-brightgreen.svg" alt="badge of hiring advertisement of 3yourmind" /></a>
<a href="https://github.com/3YOURMIND/django-migration-linter/stargazers"><img src="https://img.shields.io/github/stars/3YOURMIND/django-migration-linter.svg?style=social&label=Stars" alt="badge of github star" /></a>

## Dependencies

<p><details>
  <summary><b>Needed software (in PATH)</b></summary>

  * `python`
  * `git` (if you specify a git identifier)
</details></p>

The linter will try to detect if the project is a django project and is versioned with git.

## Installation

<p><details><summary><b>Using pip</b></summary>
  <pre><code>pip install django-migration-linter</code></pre>
</details></p>

## Usage

`django-migration-linter DJANGO_PROJECT_FOLDER [GIT_COMMIT_ID] [--ignore-name-contains=IGNORE_NAME_CONTAINS] [--include-apps INCLUDE_APPS [INCLUDE_APPS ...] | --exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]]`

| Parameter | Description |
| -- | -- |
| `DJANGO_PROJECT_FOLDER` | An absolute or relative path to the django project. |
| `GIT_COMMIT_ID` | If specified, only migrations since this commit will be taken into account. If not specified, the initial repo commit will be used. |
| `--ignore-name-contains IGNORE_NAME_CONTAINS` | Ignore migrations containing this name |
| `--ignore-name IGNORE_NAME [IGNORE_NAME ...]` | Ignore migrations with exactly one of these names |
| `--include-apps INCLUDE_APPS [INCLUDE_APPS ...]` | Check only migrations that are in the specified django apps |
| `--exclude-apps EXCLUDE_APPS [EXCLUDE_APPS ...]` | Ignore migrations that are in the specified django apps |
| `--verbose` or `-v` | print more information during execution |
| `--database DATABASE` | Specify the database for which to generate the SQL. Defaults to *default* |

## Examples

3YOURMIND is running this on [Bitbucket Pipelines](https://bitbucket.org/product/features/pipelines) with every build getting triggered in this environment.

![](https://i.imgur.com/ocLpQXP.png)

## Tests

The easiest way to run the tests is to invoke [py.test](https://docs.pytest.org/en/latest/).

More tests are always welcome.

## License

*django-migration-linter* is released under the [Apache 2.0 License](./LICENSE).
