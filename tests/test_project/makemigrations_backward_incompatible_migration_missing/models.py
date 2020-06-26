from django.db import models


class A(models.Model):
    x = models.IntegerField()
    new_field = models.CharField(null=False, default="empty", max_length=255)
