# Backward incompatible migrations

The linter analyses your migrations and checks the SQL for:

- Added `NOT NULL` columns, which don't have a DEFAULT value
- Dropping columns
- Dropping tables
- Renaming columns
- Renaming tables
- Altering columns (which can be backward compatible and potentially ignored)
- Adding a unique constraint

Those are the most important and frequent backward incompatible migrations.
We are happy to add more if you can specify them to us.


## Warnings

On data migrations, the linter will show a warning when:
* you are missing a reverse migration
* the RunPython arguments do not respect the naming convention `apps, schema_editor`
* the model variable name is different from the model class name in the `get_model` call

## Codes

You can ignore check through the `--exclude-migration-test` option and specifying any of the codes:

|               Code                |            Description                                               |
|-----------------------------------|----------------------------------------------------------------------|
|`NOT_NULL`                         | Not NULL constraint on columns
|`DROP_COLUMN`                      | Dropping columns
|`DROP_TABLE`                       | Dropping tables
|`RENAME_COLUMN`                    | Renaming columns
|`RENAME_TABLE`                     | Renaming tables
|`ALTER_COLUMN`                     | Altering columns (could be backward compatible)
|`ADD_UNIQUE`                       | Add unique constraints
|`RUNPYTHON_REVERSIBLE`             | RunPython data migration is not reversible (missing reverse code)
|`RUNPYTHON_ARGS_NAMING_CONVENTION` | By convention, RunPython names two arguments: apps, schema_editor
|`RUNPYTHON_MODEL_IMPORT`           | Missing apps.get_model() calls for model
|`RUNPYTHON_MODEL_VARIABLE_NAME`    | The model variable name is different from the model class itself
|`RUNSQL_REVERSIBLE`                | RunSQL data migration is not reversible (missing reverse SQL)
|`CREATE_INDEX`                     | Creating an index without the concurrent keyword will lock the table and may generate downtime
|`DROP_INDEX`                       | Dropping an index without the concurrent keyword will lock the table and may generate downtime
