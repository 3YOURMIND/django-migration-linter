# Publishing the package

A small note on how the linter is usually published to PyPi:

- `python3 setup.py sdist bdist_wheel --universal`
- `twine upload dist/django_migration_linter-X.Y.Z-py2.py3-none-any.whl dist/django-migration-linter-X.Y.Z.tar.gz`

