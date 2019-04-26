from django.db import models


class A(models.Model):
    null_field = models.IntegerField(null=True)
    new_null_field = models.IntegerField(null=True)
