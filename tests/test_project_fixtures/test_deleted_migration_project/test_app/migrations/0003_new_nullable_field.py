from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [('test_app', '0001_initial'),]

    operations = [
        migrations.AddField(
            model_name='a',
            name='new_char_nullable_test_field',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
