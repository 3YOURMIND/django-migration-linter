# Cache

By default, the linter uses a cache to prevent linting the same migration multiple times.
The default location of the cache on Linux is
`/home/<username>/.cache/django-migration-linter/<version>/<ldjango-project>_<database_name>.pickle`.

Since the linter uses hashes of the file's content, modifying a migration file will re-run the linter on that migration.
If you want to run the linter without cache, use the flag `--no-cache`.
If you want to invalidate the cache, delete the cache folder.
The cache folder can also be defined manually through the `--cache-path` option.
