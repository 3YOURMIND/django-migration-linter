# Copyright 2019 3YOURMIND GmbH

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

# http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.db.migrations.operations.base import Operation

IGNORE_MIGRATION_SQL = "select 1; -- dml ignores this migration"


class IgnoreMigration(Operation):

    reversible = True
    # Must be true to be generated through the sqlmigrate command
    reduces_to_sql = True

    def state_forwards(self, app_label, state):
        pass

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(IGNORE_MIGRATION_SQL)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        schema_editor.execute(IGNORE_MIGRATION_SQL + " (reversed)")

    def describe(self):
        return "The Django migration linter will ignore this migration"
