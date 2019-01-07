from django.db import models

class C(models.Model):
	not_null_field = models.IntegerField(null=False)
