from __future__ import annotations

import unittest

from django_migration_linter.sql_analyser import (
    analyse_sql_statements,
    get_sql_analyser_class,
)


class SqlAnalyserTestCase(unittest.TestCase):
    database_vendor = "default"

    def analyse_sql(self, sql):
        if isinstance(sql, str):
            sql = sql.splitlines()
        return analyse_sql_statements(
            get_sql_analyser_class(self.database_vendor),
            sql_statements=sql,
        )

    def assertValidSql(self, sql, allow_warnings=False):
        errors, _, warnings = self.analyse_sql(sql)
        self.assertEqual(0, len(errors), f"Found errors in sql: {errors}")
        if not allow_warnings:
            self.assertEqual(0, len(warnings), f"Found warnings in sql: {warnings}")

    def assertBackwardIncompatibleSql(self, sql, code=None):
        errors, _, _ = self.analyse_sql(sql)
        self.assertNotEqual(0, len(errors), "Found no errors in sql")
        if code:
            self.assertTrue(
                any(err.code == code for err in errors),
                "Didn't find error code {} in returned errors ({})".format(
                    code, [err.code for err in errors]
                ),
            )

    def assertWarningSql(self, sql, code=None):
        _, _, warnings = self.analyse_sql(sql)
        self.assertNotEqual(0, len(warnings), "Found no warnings in sql")
        if code:
            self.assertTrue(
                any(warning.code == code for warning in warnings),
                "Didn't find error code {} in returned errors ({})".format(
                    code, [warning.code for warning in warnings]
                ),
            )


class MySqlAnalyserTestCase(SqlAnalyserTestCase):
    database_vendor = "mysql"

    def test_alter_column(self):
        sql = "ALTER TABLE `app_alter_column_a` MODIFY `field` varchar(10) NULL;"
        self.assertValidSql(sql)

    def test_drop_not_null(self):
        sql = "ALTER TABLE `app_alter_column_drop_not_null_a` MODIFY `not_null_field` integer NULL;"
        self.assertValidSql(sql)

    def test_add_not_null(self):
        sql = [
            "ALTER TABLE `app_add_not_null_column_a` ADD COLUMN `new_not_null_field` integer DEFAULT 1 NOT NULL;",
            "ALTER TABLE `app_add_not_null_column_a` ALTER COLUMN `new_not_null_field` DROP DEFAULT;",
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_add_not_null_without_dropping_default(self):
        sql = (
            "ALTER TABLE `app_add_not_null_column_a` ADD COLUMN `new_not_null_field` integer DEFAULT 1 NOT NULL;",
        )
        self.assertValidSql(sql)

        sql = "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ADD COLUMN `not_null_field_db_default` integer DEFAULT (PI()) NOT NULL;"
        self.assertValidSql(sql)

    def test_add_not_null_followed_by_default(self):
        sql = [
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ADD COLUMN `new_not_null_field` integer DEFAULT 1 NOT NULL;",
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ALTER COLUMN `new_not_null_field` DROP DEFAULT;",
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ALTER COLUMN `new_not_null_field` SET DEFAULT '1';",
        ]
        self.assertValidSql(sql)

    def test_add_trigger(self):
        sql = [
            'CREATE OR REPLACE FUNCTION "public"._pgtrigger_should_ignore( trigger_name NAME ) RETURNS BOOLEAN AS $$ DECLARE _pgtrigger_ignore TEXT[]; _result BOOLEAN; BEGIN BEGIN SELECT INTO _pgtrigger_ignore CURRENT_SETTING(\'pgtrigger.ignore\'); EXCEPTION WHEN OTHERS THEN END; IF _pgtrigger_ignore IS NOT NULL THEN SELECT trigger_name = ANY(_pgtrigger_ignore) INTO _result; RETURN _result; ELSE RETURN FALSE; END IF; END; $$ LANGUAGE plpgsql; CREATE OR REPLACE FUNCTION pgtrigger_update_field_5d480() RETURNS TRIGGER AS $$ BEGIN IF ("public"._pgtrigger_should_ignore(TG_NAME) IS TRUE) THEN IF (TG_OP = \'DELETE\') THEN RETURN OLD; ELSE RETURN NEW; END IF; END IF; NEW.field := 1; RETURN NEW; END; $$ LANGUAGE plpgsql; DROP TRIGGER IF EXISTS pgtrigger_update_field_5d480 ON "app_add_trigger_a"; CREATE TRIGGER pgtrigger_update_field_5d480 BEFORE UPDATE ON "app_add_trigger_a" FOR EACH ROW WHEN (OLD."field" IS NOT DISTINCT FROM NEW."field") EXECUTE PROCEDURE pgtrigger_update_field_5d480(); COMMENT ON TRIGGER pgtrigger_update_field_5d480 ON "app_add_trigger_a" IS \'8d42224131cefae42a0fa95e72ee29e16e2058ad\'; ; COMMIT;'
        ]
        self.assertValidSql(sql)

    def test_unique_together(self):
        sql = "ALTER TABLE `app_unique_together_a` ADD CONSTRAINT `app_unique_together_a_int_field_char_field_979ac7d8_uniq` UNIQUE (`int_field`, `char_field`);"
        self.assertBackwardIncompatibleSql(sql)

        sql = "ALTER TABLE `app_unique_together_a` DROP INDEX `app_unique_together_a_int_field_char_field_979ac7d8_uniq`;"
        self.assertValidSql(sql)

    def test_unique_index(self):
        sql = 'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");'
        self.assertBackwardIncompatibleSql(sql, "ADD_UNIQUE")

        sql = [
            'CREATE TABLE "table" ("col1" integer, "col2" integer);',
            'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");',
        ]
        self.assertValidSql(sql)

    def test_add_many_to_many_field(self):
        sql = [
            "CREATE TABLE `app_add_manytomany_field_b_many_to_many`(`id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY, `b_id` integer NOT NULL, `a_id` integer NOT NULL);",
            "ALTER TABLE `app_add_manytomany_field_b_many_to_many` ADD CONSTRAINT `app_add_manytomany_f_b_id_953b185b_fk_app_add_m` FOREIGN KEY(`b_id`) REFERENCES `app_add_manytomany_field_b`(`id`);",
            "ALTER TABLE `app_add_manytomany_field_b_many_to_many` ADD CONSTRAINT `app_add_manytomany_f_a_id_4b44832a_fk_app_add_m` FOREIGN KEY(`a_id`) REFERENCES `app_add_manytomany_field_a`(`id`);",
            "ALTER TABLE `app_add_manytomany_field_b_many_to_many` ADD CONSTRAINT `app_add_manytomany_field_b_many_to_many_b_id_a_id_3e15251d_uniq` UNIQUE(`b_id`, `a_id`);",
        ]
        self.assertValidSql(sql)

    def test_make_column_not_null_with_django_default(self):
        sql = [
            "ALTER TABLE `app_drop_default_a` ALTER COLUMN `col` SET DEFAULT 'empty';",
            "UPDATE `app_drop_default_a` SET `col` = 'empty' WHERE `col` IS NULL;",
            "ALTER TABLE `app_drop_default_a` MODIFY `col` varchar(10) NOT NULL;",
            "ALTER TABLE `app_drop_default_a` ALTER COLUMN `col` DROP DEFAULT;",
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_make_column_not_null_with_lib_default(self):
        sql = [
            "ALTER TABLE `app_drop_default_a` ALTER COLUMN `col` SET DEFAULT 'empty';",
            "UPDATE `app_drop_default_a` SET `col` = 'empty' WHERE `col` IS NULL;",
            "ALTER TABLE `app_drop_default_a` MODIFY `col` varchar(10) NOT NULL;",
            "ALTER TABLE `app_drop_default_a` ALTER COLUMN `col` DROP DEFAULT;",
            "ALTER TABLE `app_drop_default_a` ALTER COLUMN `col` SET DEFAULT 'empty';",
        ]
        self.assertValidSql(sql)


class SqliteAnalyserTestCase(SqlAnalyserTestCase):
    database_vendor = "sqlite"

    def test_drop_not_null(self):
        sql = [
            'ALTER TABLE "app_alter_column_drop_not_null_a" RENAME TO "app_alter_column_drop_not_null_a__old";',
            'CREATE TABLE "app_alter_column_drop_not_null_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "not_null_field" integer NULL);',
            'INSERT INTO "app_alter_column_drop_not_null_a" ("id", "not_null_field") SELECT "id", "not_null_field" FROM "app_alter_column_drop_not_null_a__old";',
            'DROP TABLE "app_alter_column_drop_not_null_a__old";',
        ]
        self.assertValidSql(sql)

    def test_add_not_null(self):
        sql = [
            'ALTER TABLE "app_add_not_null_column_a" RENAME TO "app_add_not_null_column_a__old";',
            'CREATE TABLE "app_add_not_null_column_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "new_not_null_field" integer NOT NULL, "null_field" integer NULL);',
            'INSERT INTO "app_add_not_null_column_a" ("id", "null_field", "new_not_null_field") SELECT "id", "null_field", 1 FROM "app_add_not_null_column_a__old";',
            'DROP TABLE "app_add_not_null_column_a__old";',
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_add_not_null_without_dropping_default(self):
        sql = [
            'CREATE TABLE "new__app_add_not_null_column_followed_by_default_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "not_null_field_db_default" integer DEFAULT (PI()) NOT NULL, "field" integer NOT NULL, "not_null_field" integer NOT NULL);',
            'INSERT INTO "new__app_add_not_null_column_followed_by_default_a" ("id", "field", "not_null_field") SELECT "id", "field", "not_null_field" FROM "app_add_not_null_column_followed_by_default_a";',
            'DROP TABLE "app_add_not_null_column_followed_by_default_a";',
            'ALTER TABLE "new__app_add_not_null_column_followed_by_default_a" RENAME TO "app_add_not_null_column_followed_by_default_a";',
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_create_table_with_not_null(self):
        sql = 'CREATE TABLE "app_create_table_with_not_null_column_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "field" varchar(150) NOT NULL);'
        self.assertValidSql(sql)

    def test_rename_table(self):
        sql = 'ALTER TABLE "app_rename_table_a" RENAME TO "app_rename_table_b";'
        self.assertBackwardIncompatibleSql(sql)

    def test_alter_column(self):
        sql = [
            'ALTER TABLE "app_alter_column_a" RENAME TO "app_alter_column_a__old";',
            'CREATE TABLE "app_alter_column_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "field" varchar(10) NULL);',
            'INSERT INTO "app_alter_column_a" ("id", "field") SELECT "id", "field" FROM "app_alter_column_a__old";',
            'DROP TABLE "app_alter_column_a__old";',
        ]
        self.assertValidSql(sql)

    def test_alter_column_after_django22(self):
        sql = [
            'CREATE TABLE "new__app_alter_column_a" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "field" varchar(10) NULL);',
            'INSERT INTO "new__app_alter_column_a" ("id", "field") SELECT "id", "field" FROM "app_alter_column_a";',
            'DROP TABLE "app_alter_column_a";',
            'ALTER TABLE "new__app_alter_column_a" RENAME TO "app_alter_column_a";',
        ]
        self.assertValidSql(sql)

    def test_unique_together(self):
        sql = 'CREATE UNIQUE INDEX "app_unique_together_a_int_field_char_field_979ac7d8_uniq" ON "app_unique_together_a" ("int_field", "char_field");'
        self.assertBackwardIncompatibleSql(sql)

        sql = 'DROP INDEX "app_unique_together_a_int_field_char_field_979ac7d8_uniq";'
        self.assertValidSql(sql)

    def test_unique_index(self):
        sql = 'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");'
        self.assertBackwardIncompatibleSql(sql, "ADD_UNIQUE")

        sql = [
            'CREATE TABLE "table" ("col1" integer, "col2" integer);',
            'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");',
        ]
        self.assertValidSql(sql)

    def test_add_many_to_many_field(self):
        sql = [
            'CREATE TABLE "app_add_manytomany_field_b_many_to_many"("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "b_id" integer NOT NULL REFERENCES "app_add_manytomany_field_b"("id") DEFERRABLE INITIALLY DEFERRED, "a_id" integer NOT NULL REFERENCES "app_add_manytomany_field_a"("id") DEFERRABLE INITIALLY DEFERRED);',
            'CREATE UNIQUE INDEX "app_add_manytomany_field_b_many_to_many_b_id_a_id_3e15251d_uniq" ON "app_add_manytomany_field_b_many_to_many"("b_id", "a_id");',
            'CREATE INDEX "app_add_manytomany_field_b_many_to_many_b_id_953b185b" ON "app_add_manytomany_field_b_many_to_many"("b_id");',
            'CREATE INDEX "app_add_manytomany_field_b_many_to_many_a_id_4b44832a" ON "app_add_manytomany_field_b_many_to_many"("a_id");',
        ]
        self.assertValidSql(sql)


class PostgresqlAnalyserTestCase(SqlAnalyserTestCase):
    database_vendor = "postgresql"

    def test_alter_column(self):
        sql = 'ALTER TABLE "app_alter_column_a" ALTER COLUMN "field" TYPE varchar(10) USING "field"::varchar(10);'
        self.assertBackwardIncompatibleSql(sql)

    def test_add_not_null_without_dropping_default(self):
        sql = 'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ADD COLUMN "not_null_field_db_default" integer DEFAULT (PI()) NOT NULL;'
        self.assertValidSql(sql)

    def test_not_null_followed_by_default(self):
        sql = [
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ADD COLUMN "not_null_field" integer DEFAULT 1 NOT NULL;',
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ALTER COLUMN "not_null_field" DROP DEFAULT;',
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ALTER COLUMN "not_null_field" SET DEFAULT \'1\';',
        ]
        self.assertValidSql(sql)

    def test_field_to_not_null_with_dropped_default(self):
        sql = [
            'ALTER TABLE "api_example_example" ALTER COLUMN "foo_id" SET DEFAULT 42;',
            'UPDATE "example_example" SET "foo_id" = 42 WHERE "foo_id" IS NULL;',
            'ALTER TABLE "example_example" ALTER COLUMN "foo_id" SET NOT NULL;',
            'ALTER TABLE "example_example" ALTER COLUMN "foo_id" DROP DEFAULT;',
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_onetoonefield_to_not_null(self):
        sql = [
            'ALTER TABLE "example_example" ALTER COLUMN "foo" SET NOT NULL;',
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_drop_not_null(self):
        sql = 'ALTER TABLE "app_alter_column_drop_not_null_a" ALTER COLUMN "not_null_field" DROP NOT NULL;'
        self.assertValidSql(sql)

    def test_unique_together(self):
        sql = 'ALTER TABLE "app_unique_together_a" ADD CONSTRAINT "app_unique_together_a_int_field_char_field_979ac7d8_uniq" UNIQUE ("int_field", "char_field");'
        self.assertBackwardIncompatibleSql(sql)

        sql = 'ALTER TABLE "app_unique_together_a" DROP CONSTRAINT "app_unique_together_a_int_field_char_field_979ac7d8_uniq";'
        self.assertValidSql(sql)

    def test_unique_index(self):
        sql = 'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");'
        self.assertBackwardIncompatibleSql(sql, "ADD_UNIQUE")

        sql = [
            'CREATE TABLE "table" ("col1" integer, "col2" integer);',
            'CREATE UNIQUE INDEX "index_name" ON "table" ("col1", "col2");',
        ]
        self.assertValidSql(sql)

    def test_add_many_to_many_field(self):
        sql = [
            'CREATE TABLE "app_add_manytomany_field_b_many_to_many"("id" serial NOT NULL PRIMARY KEY, "b_id" integer NOT NULL, "a_id" integer NOT NULL);',
            'ALTER TABLE "app_add_manytomany_field_b_many_to_many" ADD CONSTRAINT "app_add_manytomany_f_b_id_953b185b_fk_app_add_m" FOREIGN KEY("b_id") REFERENCES "app_add_manytomany_field_b"("id") DEFERRABLE INITIALLY DEFERRED;',
            'ALTER TABLE "app_add_manytomany_field_b_many_to_many" ADD CONSTRAINT "app_add_manytomany_f_a_id_4b44832a_fk_app_add_m" FOREIGN KEY("a_id") REFERENCES "app_add_manytomany_field_a"("id") DEFERRABLE INITIALLY DEFERRED;',
            'ALTER TABLE "app_add_manytomany_field_b_many_to_many" ADD CONSTRAINT "app_add_manytomany_field_b_many_to_many_b_id_a_id_3e15251d_uniq" UNIQUE("b_id", "a_id");',
            'CREATE INDEX "app_add_manytomany_field_b_many_to_many_b_id_953b185b" ON "app_add_manytomany_field_b_many_to_many"("b_id");',
            'CREATE INDEX "app_add_manytomany_field_b_many_to_many_a_id_4b44832a" ON "app_add_manytomany_field_b_many_to_many"("a_id");',
        ]
        self.assertValidSql(sql, allow_warnings=True)

    def test_make_column_not_null_with_django_default(self):
        sql = [
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" SET DEFAULT \'empty\';',
            'UPDATE "app_drop_default_a" SET "col" = \'empty\' WHERE "col" IS NULL;',
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" SET NOT NULL;',
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" DROP DEFAULT;',
        ]
        self.assertBackwardIncompatibleSql(sql)

    def test_make_column_not_null_with_lib_default(self):
        sql = [
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" SET DEFAULT \'empty\';',
            'UPDATE "app_drop_default_a" SET "col" = \'empty\' WHERE "col" IS NULL;',
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" SET NOT NULL;',
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" DROP DEFAULT;',
            'ALTER TABLE "app_drop_default_a" ALTER COLUMN "col" SET DEFAULT `\'empty\';',
        ]
        self.assertValidSql(sql)

    def test_create_index_non_concurrently(self):
        sql = "CREATE INDEX ON films ((lower(title)));"
        self.assertWarningSql(sql)
        sql = "CREATE UNIQUE INDEX title_idx ON films (title);"
        self.assertWarningSql(sql)

    def test_create_index_non_concurrently_with_table_creation(self):
        sql = [
            'CREATE TABLE "films" ("title" text);',
            'CREATE INDEX ON "films" ((lower("title")));',
        ]
        self.assertValidSql(sql)
        sql = [
            'CREATE TABLE "some_table" ("title" text);',
            'CREATE INDEX ON "films" ((lower("title")));',
        ]
        self.assertWarningSql(sql)
        sql = [
            'CREATE TABLE "films" ("title" text);',
            'CREATE INDEX ON "some_table" ((lower("title")));',
        ]
        self.assertWarningSql(sql)

    def test_create_index_concurrently(self):
        sql = "CREATE INDEX CONCURRENTLY ON films (lower(title));"
        self.assertValidSql(sql)
        sql = "CREATE UNIQUE INDEX CONCURRENTLY title_idx ON films (title);"
        self.assertValidSql(sql)

    def test_create_index_concurrently_where(self):
        sql = 'CREATE INDEX CONCURRENTLY "index_name" ON "table_name" ("a_column") WHERE ("some_column" IS NOT NULL);'
        self.assertValidSql(sql)

    def test_create_unique_index_concurrently_where(self):
        sql = 'CREATE UNIQUE INDEX CONCURRENTLY "index_name" ON "table_name" ("a_column") WHERE ("some_column" IS NOT NULL);'
        self.assertBackwardIncompatibleSql(sql, "ADD_UNIQUE")

    def test_drop_index_non_concurrently(self):
        sql = "DROP INDEX ON films"
        self.assertWarningSql(sql)

    def test_drop_index_concurrently(self):
        sql = "DROP INDEX CONCURRENTLY ON films;"
        self.assertValidSql(sql)

    def test_reindex(self):
        sql = "REINDEX INDEX my_index;"
        self.assertWarningSql(sql)
        sql = "REINDEX TABLE my_table;"
        self.assertWarningSql(sql)

    def test_create_index_exclusive(self):
        sql = [
            "BEGIN;",
            'ALTER TABLE "users" ADD COLUMN "email" varchar(254) NULL;',
            'CREATE INDEX "user_email" ON "users" ("email");',
            "COMMIT;",
        ]
        self.assertWarningSql(sql, code="CREATE_INDEX_EXCLUSIVE")

    def test_create_concurrently_index_exclusive(self):
        sql = [
            "BEGIN;",
            'ALTER TABLE "users" ADD COLUMN "email" varchar(254) NULL;',
            # Counter-intuitively, concurrent index creation can take *longer*.
            # It's especially important that we flag an exclusive lock being held.
            'CREATE INDEX CONCURRENTLY "user_email" ON "users" ("email");',
            "COMMIT;",
        ]
        self.assertWarningSql(sql, code="CREATE_INDEX_EXCLUSIVE")

    def test_create_index_exclusive_no_lock(self):
        sql = [
            'ALTER TABLE "users" ADD COLUMN "email" varchar(254) NULL;',
            'CREATE INDEX "user_email" ON "users" ("email");',
        ]
        # Will warn about `CREATE_INDEX`, but *not* `CREATE_INDEX_EXCLUSIVE`
        self.assertValidSql(sql, allow_warnings=True)

    def test_create_index_exclusive_concurrently_no_lock(self):
        sql = [
            'ALTER TABLE "users" ADD COLUMN "email" varchar(254) NULL;',
            'CREATE INDEX CONCURRENTLY "user_email" ON "users" ("email");',
        ]
        self.assertValidSql(sql)


class SqlUtilsTestCase(unittest.TestCase):
    def test_unknown_analyser_string(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unknown SQL analyser 'unknown'. Known values: 'sqlite','mysql','postgresql'",
        ):
            get_sql_analyser_class("db", "unknown")

    def test_unsupported_db_vendor(self):
        with self.assertRaisesRegex(
            ValueError,
            "Unsupported database vendor 'unknown'. Try specifying an SQL analyser.",
        ):
            get_sql_analyser_class("unknown")
