# Generated by Django 4.1.4 on 2023-06-09 05:58

from decimal import Decimal
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('countries', '0001_initial'),
        ('currency', '0002_alter_currency_is_primary_exchange_rate_currency_and_more'),
        ('courses', '0037_alter_coursechangehistory_current_value'),
    ]

    operations = [
        migrations.CreateModel(
            name='GeoLocations',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('status', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='countries', to='countries.country')),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='currencies', to='currency.currency')),
            ],
            options={
                'db_table': 'geo_locations',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='GeoPricing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('currency_convert', models.BooleanField(default=True)),
                ('status', models.BooleanField(default=True)),
                ('is_deleted', models.BooleanField(default=False)),
                ('geo_location', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='geo_pricing', to='geopricing.geolocations')),
            ],
            options={
                'db_table': 'geo_pricing',
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='GeoPricingTiers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('date_updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('percentage', models.DecimalField(decimal_places=0, default=Decimal('0'), max_digits=5, validators=[django.core.validators.MinValueValidator(-100), django.core.validators.MaxValueValidator(100)])),
                ('is_deleted', models.BooleanField(default=False)),
                ('geo_pricing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='geo_pricing_tier', to='geopricing.geopricing')),
                ('pricing_tier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='geo_pricing_tier_course', to='courses.courseprice')),
            ],
            options={
                'db_table': 'geo_pricing_tiers',
                'ordering': ['-id'],
            },
        ),
        migrations.AddConstraint(
            model_name='geolocations',
            constraint=models.UniqueConstraint(fields=('country', 'currency'), name='geolocation_country_currency_constraint'),
        ),
    ]
