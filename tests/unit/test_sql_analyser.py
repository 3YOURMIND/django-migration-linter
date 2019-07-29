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

import unittest

from django_migration_linter.sql_analyser import analyse_sql_statements


class SqlAnalyserTestCase(unittest.TestCase):
    database_vendor = "default"

    def analyse_sql(self, sql):
        if isinstance(sql, str):
            sql = sql.splitlines()
        return analyse_sql_statements(
            sql_statements=sql, database_vendor=self.database_vendor
        )

    def assertValidSql(self, sql):
        errors, _ = self.analyse_sql(sql)
        self.assertEqual(0, len(errors), "Found errors in sql: {}".format(errors))

    def assertBackwardIncompatibleSql(self, sql):
        errors, _ = self.analyse_sql(sql)
        self.assertNotEqual(0, len(errors), "Found no errors in sql")


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

    def test_add_not_null_followed_by_default(self):
        sql = [
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ADD COLUMN `new_not_null_field` integer DEFAULT 1 NOT NULL;",
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ALTER COLUMN `new_not_null_field` DROP DEFAULT;",
            "ALTER TABLE `app_add_not_null_column_followed_by_default_a` ALTER COLUMN `new_not_null_field` SET DEFAULT '1';",
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


class PostgresqlAnalyserTestCase(SqlAnalyserTestCase):
    database_vendor = "postgresql"

    def test_alter_column(self):
        sql = 'ALTER TABLE "app_alter_column_a" ALTER COLUMN "field" TYPE varchar(10) USING "field"::varchar(10);'
        self.assertBackwardIncompatibleSql(sql)

    def test_not_null_followed_by_default(self):
        sql = [
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ADD COLUMN "not_null_field" integer DEFAULT 1 NOT NULL;',
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ALTER COLUMN "not_null_field" DROP DEFAULT;',
            'ALTER TABLE "app_add_not_null_column_followed_by_default_a" ALTER COLUMN "not_null_field" SET DEFAULT \'1\';',
        ]
        self.assertValidSql(sql)

    def test_drop_not_null(self):
        sql = 'ALTER TABLE "app_alter_column_drop_not_null_a" ALTER COLUMN "not_null_field" DROP NOT NULL;'
        self.assertValidSql(sql)
