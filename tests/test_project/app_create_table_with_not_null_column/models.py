from __future__ import annotations

from django.db import models


class A(models.Model):
    field = models.CharField(max_length=150, null=False)
