from __future__ import annotations

from django.db import models


class B(models.Model):
    field = models.IntegerField()
