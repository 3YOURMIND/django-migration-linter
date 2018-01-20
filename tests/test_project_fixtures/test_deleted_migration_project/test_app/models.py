from django.db import models

class A(models.Model):
	null_field = models.IntegerField(null=True)
	new_not_null_field = models.IntegerField(null=False)
	new_char_nullable_test_field = models.CharField(max_length=30, null=True)
