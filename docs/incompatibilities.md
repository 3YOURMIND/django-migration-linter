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

You can ignore checks through the `--exclude-migration-tests` option by specifying any of the codes:

|               Code                |            Description                                               |    Default type      |
|-----------------------------------|----------------------------------------------------------------------|----------------------|
|`NOT_NULL`                         | Not NULL constraint on columns | Error
|`DROP_COLUMN`                      | Dropping columns | Error
|`DROP_TABLE`                       | Dropping tables | Error
|`RENAME_COLUMN`                    | Renaming columns | Error
|`RENAME_TABLE`                     | Renaming tables | Error
|`ALTER_COLUMN`                     | Altering columns (could be backward compatible) | Error
|`ADD_UNIQUE`                       | Add unique constraints | Error
|`RUNPYTHON_REVERSIBLE`             | RunPython data migration is not reversible (missing reverse code) | Warning
|`RUNPYTHON_ARGS_NAMING_CONVENTION` | By convention, RunPython names two arguments: apps, schema_editor | Warning
|`RUNPYTHON_MODEL_IMPORT`           | Missing apps.get_model() calls for model | Error
|`RUNPYTHON_MODEL_VARIABLE_NAME`    | The model variable name is different from the model class itself | Warning
|`RUNSQL_REVERSIBLE`                | RunSQL data migration is not reversible (missing reverse SQL) | Warning
|`CREATE_INDEX`                     | (Postgresql specific) Creating an index without the concurrent keyword will lock the table and may generate downtime | Warning
|`DROP_INDEX`                       | (Postgresql specific) Dropping an index without the concurrent keyword will lock the table and may generate downtime | Warning
|`REINDEX`                          | (Postgresql specific) Reindexing will lock the table and may generate downtime | Warning
