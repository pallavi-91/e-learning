# Generated by Django 4.1.4 on 2023-05-06 10:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0018_remove_instructor_instructor_consent'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='instructor_consent',
            field=models.JSONField(default=dict),
        ),
    ]
