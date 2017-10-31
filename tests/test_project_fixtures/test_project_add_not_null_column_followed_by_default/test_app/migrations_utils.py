from django.db.migrations.operations.base import Operation
from django.utils.functional import cached_property


class AddDefaultValue(Operation):
    reversible = True

    sql_base = "ALTER TABLE `{0}` ALTER COLUMN `{1}` SET DEFAULT '{2}';"
    sql_base_reverse = "ALTER TABLE `{0}` ALTER COLUMN `{1}` DROP DEFAULT;"

    def __init__(self, model_name, name, value):
        self.model_name = model_name
        self.name = name
        self.value = value

    def deconstruct(self):
        kwargs = {
            'model_name': self.model_name,
            'name': self.name,
            'value': self.value
        }
        return (
            self.__class__.__name__,
            [],
            kwargs
        )

    @classmethod
    def is_correct_vendor(cls, vendor):
        #return vendor.startswith('mysql') or vendor.startswith('postgre')
        return True

    def state_forwards(self, app_label, state):
        """
        Take the state from the previous migration, and mutate it
        so that it matches what this migration would perform.
        """
        # Nothing to do
        # because the field should have the default setted anyway
        pass

    def database_forwards(
            self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the normal
        (forwards) direction.
        """
        if self.is_correct_vendor(schema_editor.connection.vendor):
            to_model = to_state.apps.get_model(app_label, self.model_name)
            sql_query = self.sql_base.format(
                to_model._meta.db_table, self.name, self.value)
            schema_editor.execute(sql_query)

    def database_backwards(
            self, app_label, schema_editor, from_state, to_state):
        """
        Perform the mutation on the database schema in the reverse
        direction - e.g. if this were CreateModel, it would in fact
        drop the model's table.
        """
        if self.is_correct_vendor(schema_editor.connection.vendor):
            to_model = to_state.apps.get_model(app_label, self.model_name)
            sql_query = self.sql_base_reverse.format(
                to_model._meta.db_table, self.name)
            schema_editor.execute(sql_query)

    def describe(self):
        """
        Output a brief summary of what the action does.
        """
        return 'Add to field {0} the default value {1}'.format(
            self.name, self.value)
