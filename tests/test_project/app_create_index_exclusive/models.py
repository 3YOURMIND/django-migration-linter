from __future__ import annotations

from django.db import models


class User(models.Model):
    name = models.TextField()
    email = models.EmailField(db_index=True, null=True)
