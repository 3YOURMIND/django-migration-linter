from __future__ import annotations

from django.db import models
from django.db.models import Index


class User(models.Model):
    name = models.TextField()
    email = models.EmailField(null=True)

    class Meta:
        indexes = [Index("email", name="email")]
