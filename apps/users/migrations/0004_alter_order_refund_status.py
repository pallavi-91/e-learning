# Generated by Django 4.1.4 on 2023-02-10 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_userclass_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='refund_status',
            field=models.CharField(blank=True, choices=[('Pending', 'Refund Pending'), ('Approved', 'Refund Approved'), ('Refunded', 'Refund Success'), ('Rejected', 'Refund Rejected'), ('Cancelled', 'Refund Canceled'), ('Chargeback', 'Refund Chargeback'), ('Reconciliation', 'Refund Reconcile')], max_length=30, null=True),
        ),
    ]
