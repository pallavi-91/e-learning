# Generated by Django 4.1.4 on 2023-02-22 18:21

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0008_category_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='code',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
