# Publishing the package

A small note on how the linter is usually published to PyPi:

- `rm -r django_migration_linter.egg-info/`
- `pip install wheel twine`
- `python3 setup.py sdist bdist_wheel --universal`
- `twine upload dist/django_migration_linter-X.Y.Z-py3-none-any.whl dist/django-migration-linter-X.Y.Z.tar.gz`
