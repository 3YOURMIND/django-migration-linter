from appdirs import user_cache_dir

__version__ = "1.4.1"

DEFAULT_CACHE_PATH = user_cache_dir("django-migration-linter", version=__version__)
