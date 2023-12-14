# Generated by Django 4.1.4 on 2023-02-22 17:39

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('shares', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='shareprices',
            name='code',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]