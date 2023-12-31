# Generated by Django 4.1.4 on 2023-04-28 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_userclass_certificate_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='instructor',
            name='group_name',
            field=models.CharField(blank=True, choices=[('default', 'Instructor (Default)'), ('premium', 'Premium Instructor'), ('partner', 'Partner Instructor')], default='default', max_length=20),
        ),
    ]
