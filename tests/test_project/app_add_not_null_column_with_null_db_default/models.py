from __future__ import annotations

from django.db import models
from django.db.models.functions import Pi


class A(models.Model):
    field = models.IntegerField()
    not_null_field_db_default_null = models.IntegerField(null=False, db_default=None)
