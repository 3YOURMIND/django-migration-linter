from __future__ import annotations

from django.db import models


class A(models.Model):
    int_field = models.IntegerField()
    char_field = models.CharField(max_length=255)
