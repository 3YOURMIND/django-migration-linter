# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-04-14 14:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("app_drop_column", "0001_initial")]

    operations = [migrations.RemoveField(model_name="a", name="field_b")]
