# Generated by Django 4.1.4 on 2023-05-04 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0031_rename_index_coursechangehistory_intended_learners'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursechangehistory',
            name='resolved',
            field=models.BooleanField(default=False),
        ),
    ]
