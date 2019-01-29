from django.db import models

class A(models.Model):
	not_null_field = models.IntegerField(null=False)


class B(models.Model):
	not_null_fk = models.ForeignKey(to=A, null=False, on_delete=models.CASCADE, related_name='nn_b')
	null_fk = models.ForeignKey(to=A, null=True, on_delete=models.CASCADE, related_name='b')
