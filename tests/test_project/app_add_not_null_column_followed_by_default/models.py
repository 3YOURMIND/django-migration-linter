# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class A(models.Model):
    field = models.IntegerField()
    not_null_field = models.IntegerField(null=False, default=1)
