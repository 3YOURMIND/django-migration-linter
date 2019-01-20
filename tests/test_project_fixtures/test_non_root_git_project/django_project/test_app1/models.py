from django.db import models

class A(models.Model):
	null_field = models.IntegerField()
	null_field_2 = models.IntegerField(default=1)
	non_null_field = models.IntegerField(null=True)
