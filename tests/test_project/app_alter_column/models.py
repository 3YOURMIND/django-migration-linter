# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class A(models.Model):
    field = models.CharField(null=True, max_length=10)
