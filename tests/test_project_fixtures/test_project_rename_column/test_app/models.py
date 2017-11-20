from django.db import models

class A(models.Model):
	new_name_field = models.IntegerField(null=True)
