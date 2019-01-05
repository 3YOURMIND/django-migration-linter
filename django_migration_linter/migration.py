from django_migration_linter.utils import split_migration_path


class Migration(object):
    def __init__(self, abs_path):
        self.abs_path = abs_path
        self.app_name, self.name = split_migration_path(self.abs_path)

    def __lt__(self, other):
        if not isinstance(other, Migration):
            return NotImplemented
        return self.abs_path < other.abs_path
