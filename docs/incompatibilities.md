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
| `CREATE_INDEX_EXCLUSIVE`           | (Postgresql specific) Creating an index in a transaction (after an `EXCLUSIVE` lock) prolongs the exclusive lock     | Warning      |
| `DROP_INDEX`                       | (Postgresql specific) Dropping an index without the concurrent keyword will lock the table and may generate downtime | Warning      |
| `REINDEX`                          | (Postgresql specific) Reindexing will lock the table and may generate downtime                                       | Warning      |


## Details about backward incompatibilities

This section will go into the depth of the different check the migration linter makes.
The base hypotheses of these cases are:
- in a production system, you cannot deploy your database(s) (DB) and code server(s) simultaneously
- you deploy your DB first, as there are very few cases in which deploying the code first is viable when database operations are required

### :arrow_forward: Adding `NOT NULL` column without default value

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
But Django actually uses the default value to fill the new column on existing rows and to set an unspecified column value to its default.
The latter is done at the application level, by Django and not by the database because the default value was dropped during migration.
You can read more about this in the [Django and its default values blog post](https://medium.com/botify-labs/django-and-its-default-values-c21a13cff9f).

:white_check_mark: **Solutions**:
- Make the column nullable, and later do a multistep process later to make it NOT NULL once your code is aware of it.

### :arrow_forward: Adding `NOT NULL` column **with** default value

**Forward migration**:
1. update your DB to add a `NOT NULL` column with a Django default
2. before code migration, your Django code will not specify the new column when inserting a row, and Django is not aware of the default value
   => error `column cannot be null` :x:
3. once the code updated, insertion will work

**Rollback**: in the case of a rollback, you will encounter the same errors

:white_check_mark: **Solutions**:
- Make the column nullable
- Set a database default using the Django 5.0 attribute `db_default`. See the [Django docs](https://docs.djangoproject.com/en/dev/releases/5.0/#database-computed-default-values)
- Set a database default using Django's [RunSQL](https://docs.djangoproject.com/en/dev/ref/migration-operations/#django.db.migrations.operations.RunSQL)
- Set a database default using [django-add-default-value](https://github.com/3YOURMIND/django-add-default-value/)

### :arrow_forward: Dropping a column

Deletion operations often lead to errors during deployment.

**Forward migration**:
1. update your DB to drop a column
2. before code migration, your code will crash retrieving rows from this table
(because Django explicits all column names when fetching a model object) :x:
3. once the code is updated, the errors should cease

**Rollback**:
1. rollback your code
2. your code will crash retrieving rows from this table (because Django explicits all column names when fetching a model object)
3. rollback your DB to re-create the column
4. restore a backup  of your data (if available and fresh enough)

:white_check_mark: **Solutions**:
- Deprecate the column before dropping it using [django-deprecate-fields](https://github.com/3YOURMIND/django-deprecate-fields/).
This process requires to first make sure that the field is unused (for which `django-deprecate-fields` is made for).
Once the column is unsed, drop it in a migration. This migration will require to be ignored through the [IgnoreMigration](/docs/usage.md#ignoring-migrations) for instance.
- Don't actually drop the column, but fake the drop migration until you are sure you won't roll back.
Be careful :warning: fake dropping a non-nullable column without a database default will create errors once the code is not aware of the column anymore.

### :arrow_forward: Dropping a table

**Forward migration**:
1. update your DB to drop a table
2. before code migration, your code might still try to query the deleted table to fetch rows. Of course, this will crash :x:
3. once the code is updated, the errors should cease

**Rollback**:
1. rollback your code
2. your code will crash retrieving rows from this table
3. rollback your DB to re-create the table
4. restore a backup  of your data (if available and fresh enough)

:white_check_mark: **Solutions**:
- Do a multistep deletion. First, only update the code to make sure it is not querying the table anymore

### :arrow_forward: Altering a column

In some cases, altering a column can lead to backward incompatible migrations.
One of these cases is changing the column's type, which can be backward incompatible, but not necessarily.

**Forward migration**:
1. update your DB to change a string/varchar column to integer
2. before code migration, your code will crash when trying to insert strings that cannot be cast to integer implicitly :x:
3. once the code is updated, the errors should cease (because your code will probably aware that it should only use int values)

**Rollback**: shouldn't be an issue in this case, because when the code expects strings but the DB has integers, implicitly casting should be fine.
However, if the forward migration was migrating from an integer type to strings, the rollback would have involved an integer field potentially receiving string values that couldn't be cast to integers.

:white_check_mark: **Solutions**:
- create a new column with the new field settings and keep data in sync between the old and new version.
At some point, start using the new column and delete the old one once the migration went well
- multistep deployment by first ensuring that the application is only manipulating the new type and gracefully handling an incorrect value.

### :arrow_forward: Adding a unique constraint

**Forward migration**:
1. update your DB to add a unique constraint on multiple columns
2. before code migration, your code might still try to add the same value twice in the column
3. once the code is updated, the errors should cease

**Rollback**:
1. rollback your code
2. your code will crash trying to add an existing value
3. rollback your DB to drop the unique constraint, and it should work again

:white_check_mark: **Solutions**:
- Do a multistep deployment. First, make sure that the code is only pushing a value if it is unique.

### :arrow_forward: Importing a model in a RunPython migration

When doing [RunPython](https://docs.djangoproject.com/en/dev/ref/migration-operations/#runpython) operations in migrations, it is important to not do direct `import`s of model classes.
Instead, once you use the `apps.get_model` function, if the first argument of your `RunPython` function is called `apps`.

:warning: When doing a direct `import` statement, your code will use the latest version of your model class.
However, in a migration, you should be using the version of the model, at the point in time where this migration was created.
It could happen that you use a `RunPython` operation to fill a new column. But if you import that latest version of the model, this column might not exist anymore, which will break a prior migration.

:white_check_mark: **Solution**: use `apps.get_model` to get the model class

## The special case of sqlite

While on PostgreSQL and MySQL a table modification can be expressed by one `ALTER TABLE` statement, sqlite is handled in a different way.
For operations like adding a column to an existing table, Django actually generates four statements:
- creating a new table with the new schema
- copying all rows from the current table to the new one
- dropping the current table
- renaming the new table to the current table name

At the time of writing, the linter doesn't support a fine-grained detection of field alteration when using the sqlite process.
An [issue #142](https://github.com/3YOURMIND/django-migration-linter/issues/142) is already open and Django also has a [ticket about supporting sqlite ALTER functions](https://code.djangoproject.com/ticket/32502).
