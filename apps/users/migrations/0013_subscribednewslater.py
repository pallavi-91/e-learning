# Generated by Django 4.1.4 on 2023-03-23 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_alter_order_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscribedNewsLater',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('email_address', models.EmailField(max_length=250, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
