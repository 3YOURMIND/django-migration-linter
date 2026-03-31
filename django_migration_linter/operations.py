from django.db.migrations.operations.base import Operation


class IgnoreMigration(Operation):
    """
    No-op migration operation that will enable the Django Migration Linter
    to detect if the entire migration should be ignored (through code).
    """

    reversible = True
    reduces_to_sql = False
    elidable = True

    def state_forwards(self, app_label, state):
        raise Exception("Please don't use this operation. Update lint_lcv_migrations.py to exclude the migration.")

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        raise Exception("Please don't use this operation. Update lint_lcv_migrations.py to exclude the migration.")

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        raise Exception("Please don't use this operation. Update lint_lcv_migrations.py to exclude the migration.")

    def describe(self):
        return "Please don't use this operation. Update lint_lcv_migrations.py to exclude the migration."
