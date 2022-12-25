from __future__ import annotations

from django.db import models


class A(models.Model):
    field_a = models.IntegerField()
