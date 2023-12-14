# Generated by Django 4.1.4 on 2023-02-21 11:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('currency', '0001_initial'),
        ('transactions', '0006_holdtransaction_hold_transaction_status_constraint_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactions',
            name='currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='currency.Currency'),
        ),
    ]
