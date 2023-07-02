# Generated by Django 2.1.4 on 2019-03-21 20:41

from __future__ import annotations

from django.db import migrations, models

import django_migration_linter as linter


class Migration(migrations.Migration):
    dependencies = [("app_ignore_migration", "0001_initial")]

    operations = [
        linter.IgnoreMigration(),
        migrations.AddField(
            model_name="b",
            name="null_field_real",
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
