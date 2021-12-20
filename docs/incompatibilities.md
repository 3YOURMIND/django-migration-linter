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

| Code                               | Description                                                                                                          | Default type |
|------------------------------------|----------------------------------------------------------------------------------------------------------------------|--------------|
| `NOT_NULL`                         | Not NULL constraint on columns                                                                                       | Error        |
| `DROP_COLUMN`                      | Dropping columns                                                                                                     | Error        |
| `DROP_TABLE`                       | Dropping tables                                                                                                      | Error        |
| `RENAME_COLUMN`                    | Renaming columns                                                                                                     | Error        |
| `RENAME_TABLE`                     | Renaming tables                                                                                                      | Error        |
| `ALTER_COLUMN`                     | Altering columns (could be backward compatible)                                                                      | Error        |
| `ADD_UNIQUE`                       | Add unique constraints                                                                                               | Error        |
| `RUNPYTHON_REVERSIBLE`             | RunPython data migration is not reversible (missing reverse code)                                                    | Warning      |
| `RUNPYTHON_ARGS_NAMING_CONVENTION` | By convention, RunPython names two arguments: apps, schema_editor                                                    | Warning      |
| `RUNPYTHON_MODEL_IMPORT`           | Missing apps.get_model() calls for model                                                                             | Error        |
| `RUNPYTHON_MODEL_VARIABLE_NAME`    | The model variable name is different from the model class itself                                                     | Warning      |
| `RUNSQL_REVERSIBLE`                | RunSQL data migration is not reversible (missing reverse SQL)                                                        | Warning      |
| `CREATE_INDEX`                     | (Postgresql specific) Creating an index without the concurrent keyword will lock the table and may generate downtime | Warning      |
| `DROP_INDEX`                       | (Postgresql specific) Dropping an index without the concurrent keyword will lock the table and may generate downtime | Warning      |
| `REINDEX`                          | (Postgresql specific) Reindexing will lock the table and may generate downtime                                       | Warning      |


## Details about backward incompatibilities

This section will go into the depth of the different check the migration linter makes.
The base hypotheses of these cases are:
- in a production system, you cannot deploy your database(s) (DB) and code server(s) simultaneously
- you deploy your DB first, as there are very few cases in which deploying the code first is viable when database operations are required

### Adding `NOT NULL` column without default value

A frequent and error-prone operation is adding a non-nullable column to an existing table.

Adding a `NOT NULL` column **without any default value** is problematic.

**Forward migration**:
1. update your DB to add a `NOT NULL` column
2. before code migration, your Django code will not specify the new column when inserting a row
=> error `column cannot be null` :x:
3. once the code updated, insertion will work because the new column is explicitly specified by Django

**Rollback**: in the case of a rollback, you will encounter the same error.
Only rolling back the code will make all new insertions crash because Django doesn't specify the new column.

:warning: An incorrect solution is to specify simply a default value in the Django model field.
One would think that adding a default value in Django will prevent these errors.

A common misconception is that the Django default value is translated to a database default.
But Django actually uses the default value to fill new new column on existing rows and to set an unspecified column value to its default.
The latter is done at the application level, by Django and not by the database because the default value was dropped during migration.
You can read more about this in the [Django and its default values blog post](https://medium.com/botify-labs/django-and-its-default-values-c21a13cff9f).

:white_check_mark: **Solutions**:
- Make the column nullable, and later do a multistep process later to make it NOT NULL once your code is aware of it.

### Adding `NOT NULL` column **with** default value

**Forward migration**:
1. update your DB to add a `NOT NULL` column with a Django default
2. before code migration, your Django code will not specify the new column when inserting a row, and Django is not aware of the default value
   => error `column cannot be null` :x:
3. once the code updated, insertion will work

**Rollback**: in the case of a rollback, you will encounter the same errors

:white_check_mark: **Solutions**:
- Make the column nullable
- Set a database default using Django's [RunSQL](https://docs.djangoproject.com/en/dev/ref/migration-operations/#django.db.migrations.operations.RunSQL)
- Set a database default using [django-add-default-value](https://github.com/3YOURMIND/django-add-default-value/)

### Dropping a column

Deletion operations often lead to errors during deployment.

**Forward migration**:
1. update your DB to drop a column
2. your code will crash retrieving rows from this table (because Django explicits all column names when fetching a model object)
3. once the code is updated, the errors should cease

**Rollback**:
1. rollback your code
2. your code will crash retrieving rows from this table (because Django explicits all column names when fetching a model object)
3. rollback your DB to re-create the column
4. restore a backup  of your data (if available and fresh enough)

**Solutions**:
- Deprecate the column before dropping it using [django-deprecate-fields](https://github.com/3YOURMIND/django-deprecate-fields/)
- Don't actually drop the column, but fake the drop migration until you are sure you won't roll back.
Be careful /!\ fake dropping a non-nullable column without a database default will create errors once the code is not aware of the column anymore.

### Others

To be added...

## The special case of sqlite

While on PostgreSQL and MySQL a table modification can be expressed by one `ALTER TABLE` statement, sqlite is handled in a different way.
For operations like adding a column to an existing table, Django actually generates four statements:
- creating a new table with the new schema
- copying all rows from the current table to the new one
- dropping the current table
- renaming the new table to the current table name

At the time of writing, the linter doesn't support a fine-grained detection of field alteration when using the sqlite process.
An [issue #142](https://github.com/3YOURMIND/django-migration-linter/issues/142) is already open and Django also has a [ticket about supporting sqlite ALTER functions](https://code.djangoproject.com/ticket/32502).
