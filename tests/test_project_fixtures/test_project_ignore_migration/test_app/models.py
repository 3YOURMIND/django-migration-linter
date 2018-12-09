from django.db import models

class B(models.Model):
	null_field = models.IntegerField(null=True)
