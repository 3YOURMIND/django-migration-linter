# Generated by Django 2.2 on 2020-01-26 17:43

from django.db import migrations


def update_things(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app_data_migrations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(update_things),
    ]
