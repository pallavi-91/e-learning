# Generated by Django 4.1.4 on 2023-02-17 07:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_alter_transactions_options_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refundrequest',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to='transactions.transactions'),
        ),
    ]