from __future__ import annotations

from django.db import models


class A(models.Model):
    col = models.CharField(max_length=10, null=False, default="avalue")
