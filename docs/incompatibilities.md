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
