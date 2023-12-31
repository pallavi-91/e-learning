# Generated by Django 4.1.4 on 2023-04-16 08:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_userclass_certificate_alter_user_photo'),
        ('transactions', '0009_rename_gateway_transaction_id_transactions_payment_transaction_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactions',
            name='order',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='order_transactions', to='users.order'),
        ),
        migrations.AlterField(
            model_name='transactions',
            name='user_class',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transactions', to='users.userclass'),
        ),
    ]
