# Generated by Django 4.1.4 on 2023-03-12 11:02

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_userclass_archived'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='code',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]