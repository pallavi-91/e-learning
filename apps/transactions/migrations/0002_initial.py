# Generated by Django 4.1.4 on 2023-02-05 17:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('transactions', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transactions',
            name='instructor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='instructor_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='transactions',
            name='order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_transactions', to='users.order'),
        ),
        migrations.AddField(
            model_name='transactions',
            name='payment_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='transactions.paymenttype'),
        ),
        migrations.AddField(
            model_name='transactions',
            name='student',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_transactions', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='transactions',
            name='user_class',
            field=models.ForeignKey(max_length=10, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='users.userclass'),
        ),
        migrations.AddField(
            model_name='transactionpayout',
            name='payout',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='transactions.instructorpayouts'),
        ),
        migrations.AddField(
            model_name='transactionpayout',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_payout', to='transactions.transactions'),
        ),
        migrations.AddField(
            model_name='transactioncoupons',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transaction_coupons', to='transactions.transactions'),
        ),
        migrations.AddField(
            model_name='refundrequest',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to='transactions.transactions', verbose_name='Order Transaction'),
        ),
        migrations.AddField(
            model_name='refundrequest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='refund_requests', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='payoutdirecttransition',
            name='payout',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='direct_transitions', to='transactions.instructorpayouts'),
        ),
        migrations.AddField(
            model_name='payoutdirecttransition',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payout_transition', to=settings.AUTH_USER_MODEL, verbose_name='Performed By'),
        ),
        migrations.AddField(
            model_name='instructorpayouts',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payout_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Instructor'),
        ),
        migrations.AddField(
            model_name='holdtransaction',
            name='transaction',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hold', to='transactions.transactions'),
        ),
        migrations.AddField(
            model_name='holdtransaction',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hold_transactions', to=settings.AUTH_USER_MODEL, verbose_name='Hold By'),
        ),
    ]
