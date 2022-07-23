# -*- coding: utf-8 -*-


from django.db import models


class A(models.Model):
    field = models.CharField(null=True, max_length=10)
