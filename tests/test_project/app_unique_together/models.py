from django.db import models


class A(models.Model):
    int_field = models.IntegerField()
    char_field = models.CharField(max_length=255)

    # class Meta:
    #     unique_together = (("int_field", "char_field"),)
