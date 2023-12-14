# Generated by Django 4.1.4 on 2023-02-05 17:55

import apps.transactions.utility
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('currency', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='HoldTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('reason', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('Hold', 'Hold'), ('UnHold', 'Unhold')], default='Hold', max_length=15)),
            ],
            options={
                'db_table': 'payout_hold_transactions',
            },
        ),
        migrations.CreateModel(
            name='InstructorPayouts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('period', models.DateField()),
                ('status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed'), ('Pending', 'Pending'), ('Unclaimed', 'Unclaimed'), ('Returned', 'Returned'), ('On-hold', 'Onhold'), ('Blocked', 'Blocked'), ('Refunded', 'Refunded'), ('Reversed', 'Reversed'), ('Ready', 'Ready')], default='Pending', max_length=15)),
                ('payout_type', models.CharField(choices=[('Upcoming', 'Upcoming'), ('OnGoing', 'Ongoing'), ('Paid', 'Paid'), ('Failed', 'Failed'), ('Inactive', 'Inactive')], default='OnGoing', max_length=20)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('due_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'db_table': 'payouts',
            },
        ),
        migrations.CreateModel(
            name='PaymentType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('payment_gateway', models.CharField(choices=[('Paypal', 'Paypal'), ('HyperPay', 'Hyperpay')], default='Paypal', max_length=100)),
                ('payment_method', models.CharField(choices=[('Direct To Bank', 'Bank Transfer'), ('Online Transfer', 'Online Transfer'), ('Card', 'Card')], default='Card', max_length=100)),
                ('gateway_charge', models.FloatField(default=0.0)),
            ],
            options={
                'db_table': 'payment_options',
            },
        ),
        migrations.CreateModel(
            name='PayoutDirectTransition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('reason', models.TextField(blank=True)),
                ('status', models.CharField(choices=[('Mark As Paid', 'Mark As Paid'), ('Inactive Paid', 'Inactive Paid')], default='Mark As Paid', max_length=15)),
            ],
            options={
                'db_table': 'payouts_direct_pay',
            },
        ),
        migrations.CreateModel(
            name='RefundRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('status', models.CharField(choices=[('Pending', 'Refund Pending'), ('Approved', 'Refund Approved'), ('Refunded', 'Refund Success'), ('Rejected', 'Refund Rejected'), ('Cancelled', 'Refund Canceled'), ('Chargeback', 'Refund Chargeback')], default='Pending', max_length=15)),
                ('reason', models.TextField()),
                ('refund_amount', models.FloatField(default=0)),
                ('refund_type', models.CharField(choices=[('Regular Refund', 'Regular'), ('Thkee Refund', 'Thkee')], default='Regular Refund', max_length=20)),
            ],
            options={
                'db_table': 'refund_requests',
            },
        ),
        migrations.CreateModel(
            name='TransactionCoupons',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('discount', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('discount_value', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('coupon_code', models.CharField(blank=True, max_length=10, null=True)),
            ],
            options={
                'verbose_name': 'Transaction Discount',
                'db_table': 'transaction_coupons',
            },
        ),
        migrations.CreateModel(
            name='TransactionPayout',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
            ],
            options={
                'db_table': 'payouts_transactions',
            },
        ),
        migrations.CreateModel(
            name='Transactions',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('transaction_id', models.CharField(default=apps.transactions.utility.get_transaction_code, max_length=50)),
                ('refund', models.BooleanField(default=False)),
                ('refund_status', models.CharField(blank=True, choices=[('Pending', 'Refund Pending'), ('Approved', 'Refund Approved'), ('Refunded', 'Refund Success'), ('Rejected', 'Refund Rejected'), ('Cancelled', 'Refund Canceled'), ('Chargeback', 'Refund Chargeback')], max_length=30, null=True)),
                ('date_refunded', models.DateTimeField(blank=True, null=True)),
                ('type', models.CharField(choices=[('Sale', 'Sale'), ('Payout', 'Payout'), ('Refund', 'Refund')], default='Sale', max_length=50, verbose_name='Transaction Type')),
                ('status', models.CharField(choices=[('Available', 'Available'), ('Pending', 'Pending'), ('Denied', 'Denied'), ('Processing', 'Processing'), ('Success', 'Success'), ('Canceled', 'Canceled'), ('Failed', 'Failed')], default='Pending', max_length=20, verbose_name='Transaction Status')),
                ('gross_amount', models.FloatField(default=0.0)),
                ('vat_amount', models.FloatField(default=0.0)),
                ('channel', models.JSONField(default=dict)),
                ('gateway_transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('gateway_raw', models.JSONField(default=dict)),
                ('payout_status', models.CharField(choices=[('Success', 'Success'), ('Failed', 'Failed'), ('Pending', 'Pending'), ('Unclaimed', 'Unclaimed'), ('Returned', 'Returned'), ('On-hold', 'Onhold'), ('Blocked', 'Blocked'), ('Refunded', 'Refunded'), ('Reversed', 'Reversed'), ('Ready', 'Ready')], default='Pending', max_length=20)),
                ('payout_error', models.JSONField(blank=True, null=True)),
                ('currency', models.ForeignKey(max_length=10, null=True, on_delete=django.db.models.deletion.SET_NULL, to='currency.Currency')),
            ],
            options={
                'db_table': 'transactions',
            },
        ),
    ]
