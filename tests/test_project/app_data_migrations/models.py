from __future__ import annotations

from django.db import models


class MyModel(models.Model):
    myfield = models.IntegerField()
