# Generated by Django 4.1.4 on 2023-02-28 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0007_alter_transactions_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactions',
            name='gateway_charge',
            field=models.FloatField(default=0.0),
        ),
    ]
