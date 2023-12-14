# Generated by Django 4.1.4 on 2023-02-05 17:55

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InstructorGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('group_name', models.CharField(choices=[('default', 'Instructor (Default)'), ('premium', 'Premium Instructor'), ('partner', 'Partner Instructor')], default='default', max_length=20, unique=True)),
            ],
            options={
                'db_table': 'instructor_groups',
            },
        ),
        migrations.CreateModel(
            name='SharePrices',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('share_types', models.CharField(choices=[('ORGANICS', 'Organics'), ('ADS', 'Ads'), ('INSTRUCTOR_REFERRAL', 'Instructor Referral'), ('AFFILIATE', 'Affiliate'), ('STUDENT_REFERRAL', 'Student Referral')], default='ORGANICS', max_length=20)),
                ('instructor_share', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('platform_share', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('affiliate_share', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('thkee_credit', models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('group_name', models.CharField(blank=True, choices=[('default', 'Instructor (Default)'), ('premium', 'Premium Instructor'), ('partner', 'Partner Instructor')], default='default', max_length=20)),
            ],
            options={
                'db_table': 'shareprices',
                'unique_together': {('share_types', 'group_name')},
            },
        ),
    ]
