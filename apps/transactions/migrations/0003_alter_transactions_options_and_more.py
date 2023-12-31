# Generated by Django 4.1.4 on 2023-02-10 16:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('currency', '0001_initial'),
        ('users', '0004_alter_order_refund_status'),
        ('transactions', '0002_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='transactions',
            options={'ordering': ['-date_updated']},
        ),
        migrations.AlterField(
            model_name='refundrequest',
            name='status',
            field=models.CharField(choices=[('Pending', 'Refund Pending'), ('Approved', 'Refund Approved'), ('Refunded', 'Refund Success'), ('Rejected', 'Refund Rejected'), ('Cancelled', 'Refund Canceled'), ('Chargeback', 'Refund Chargeback'), ('Reconciliation', 'Refund Reconcile')], default='Pending', max_length=15),
        ),
        migrations.AlterField(
            model_name='transactions',
            name='currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='currency.Currency'),
        ),
        migrations.AlterField(
            model_name='transactions',
            name='instructor',
            field=models.ForeignKey( on_delete=django.db.models.deletion.CASCADE, related_name='instructor_transactions', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transactions',
            name='order',
            field=models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, related_name='order_transactions', to='users.order'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transactions',
            name='refund_status',
            field=models.CharField(blank=True, choices=[('Pending', 'Refund Pending'), ('Approved', 'Refund Approved'), ('Refunded', 'Refund Success'), ('Rejected', 'Refund Rejected'), ('Cancelled', 'Refund Canceled'), ('Chargeback', 'Refund Chargeback'), ('Reconciliation', 'Refund Reconcile')], max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='transactions',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='student_transactions', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transactions',
            name='user_class',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.DO_NOTHING, related_name='transactions', to='users.userclass'),
            preserve_default=False,
        ),
    ]
