from __future__ import print_function

import os
from importlib import import_module


def split_path(path):
    decomposed_path = []
    while 1:
        head, tail = os.path.split(path)
        if head == path:  # sentinel for absolute paths
            decomposed_path.insert(0, head)
            break
        elif tail == path:  # sentinel for relative paths
            decomposed_path.insert(0, tail)
            break
        else:
            path = head
            decomposed_path.insert(0, tail)

    if not decomposed_path[-1]:
        decomposed_path = decomposed_path[:-1]
    return decomposed_path


def split_migration_path(migration_path):
    from django.db.migrations.loader import MIGRATIONS_MODULE_NAME

    decomposed_path = split_path(migration_path)
    for i, p in enumerate(decomposed_path):
        if p == MIGRATIONS_MODULE_NAME:
            return decomposed_path[i - 1], os.path.splitext(decomposed_path[i + 1])[0]


def clean_bytes_to_str(byte_input):
    return byte_input.decode("utf-8").strip()


def get_migration_abspath(app_label, migration_name):
    from django.db.migrations.loader import MigrationLoader

    module_name, _ = MigrationLoader.migrations_module(app_label)
    migration_path = "{}.{}".format(module_name, migration_name)
    migration_module = import_module(migration_path)

    migration_file = migration_module.__file__
    if migration_file.endswith(".pyc"):
        migration_file = migration_file[:-1]
    return migration_file
