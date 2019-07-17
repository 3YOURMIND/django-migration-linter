from django.db import models


class A(models.Model):
    not_null_field = models.IntegerField(null=True)
