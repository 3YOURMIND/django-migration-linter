from django.db import models


class A(models.Model):
    pass


class B(models.Model):
    many_to_many = models.ManyToManyField(A)
