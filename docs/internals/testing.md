# Testing

The easiest way to run the tests is to invoke `tox` on the command line.

You will need to install the test requirements, which can be found in the ``setup.py`` file.
A good way to get started is to install the development version of the linter by doing ``pip install -e .[test]``.

To be able to fully test the linter, you will need both MySQL and PostgreSQL databases running.
You can either tweak the ``tests/test_project/settings.py`` file to get your DB settings right, or to have databases and users corresponding to the default CI users.

## Database setup

By default, the test Django project in the repository has multiple databases configured in order to make the CI tests work.
Do not hesitate to modify [the configured test databases](../../tests/test_project/settings.py).
