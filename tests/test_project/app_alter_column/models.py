from __future__ import annotations

from django.db import models


class A(models.Model):
    field = models.CharField(null=True, max_length=10)
