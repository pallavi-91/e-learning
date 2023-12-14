from functools import cached_property
from django.db import models
from django.conf import settings
from .currency_list import currency_list
from apps.countries.models import Country
from currency_converter import CurrencyConverter, SINGLE_DAY_ECB_URL
from django.db.models.signals import post_save
from apps.status.mixins import AtMostOneBooleanField, AutoCreatedUpdatedMixin
from decimal import *
from apps.currency.format import FormatCurrency
import math

# Create your models here.
class RoundingModes(models.TextChoices):
    # Rounding modes
    DEFAULT = 'decimal>=0.5', 'Roundind with 0.50 intervals'
    ROUND_A = '1.49=<decimal>=1.50', 'Roundind with 1.00 intervals (1.01-1.49 round to 1.00, 1.50-1.99 round to 2.00)'
    ROUND_B = 'decimal>=1.01', 'Roundind with 1.00 intervals (1.01-1.99 round to 2.00)'

class Currency(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = "currency"
        ordering = ['-id']
        
    name = models.CharField(max_length=200, unique=True)
    currency_code = models.CharField(max_length=20, choices=currency_list, default='USD', unique=True)
    rate = models.FloatField(default=0.0)
    rounding_type = models.CharField(max_length=100, choices=RoundingModes.choices, default=RoundingModes.DEFAULT)
    is_primary_exchange_rate_currency = AtMostOneBooleanField(default=False)
    is_primary_store_currency = AtMostOneBooleanField(default=False)
    pricing_tier_status = models.BooleanField(default=False)
    force = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    country = models.ManyToManyField(Country, blank=True)
    

    def __str__(self) -> str:
        return f"<Currency> {self.name}"

    @cached_property
    def exchange(self):
        return CurrencyConverter(SINGLE_DAY_ECB_URL, fallback_on_wrong_date=True, fallback_on_missing_rate=True)
    
    @cached_property
    def symbol(self):
        formater = FormatCurrency(self.currency_code)
        return formater.get_money_format('')

    @classmethod
    def primary_currency(cls):
        return init_currency_code()
    
    def rounding(self, value):
        frac, whole = math.modf(value)
        decimal = Decimal(frac).quantize(Decimal('.01'), rounding=ROUND_HALF_EVEN)
        
        if self.rounding_type == RoundingModes.ROUND_A:
            if decimal <= 0.49:
                value = float(whole)
            else:
                value = float(whole)+1
                
        elif self.rounding_type == RoundingModes.ROUND_B:
            value = float(Decimal(value).quantize(Decimal('.01')).to_integral(rounding=ROUND_UP))
        else:
            # Default
            value = float(Decimal(value).quantize(Decimal('1'), rounding=ROUND_HALF_UP).to_integral_value())
        return value
    
    def can_delete(self):
        return not self.classes.count() and not self.transactions.count()
 
def init_currency_code():
    primary_exchange_rate_currency = Currency.objects.filter(is_primary_exchange_rate_currency=True)
    primary_store_currency = Currency.objects.filter(is_primary_store_currency=True)
    exchange_rate_currency_code = ''
    store_currency_code = ''
    params = dict()
    if primary_exchange_rate_currency.exists():
        exchange_rate_currency_code = primary_exchange_rate_currency.first().currency_code
        params['exchange_rate_currency'] = exchange_rate_currency_code
        params['exchange_rate_currency_symbol'] = exchange_rate_currency_code
    if primary_store_currency.exists():
        store_currency_code = primary_store_currency.first().currency_code
        params['store_currency'] = store_currency_code
    
    if params:
        settings.PRIMARY_CURRENCY_CODE.update(params)
    return settings.PRIMARY_CURRENCY_CODE


def set_primary_currency(sender, instance, *args, **kwargs):
    primary_currency = settings.PRIMARY_CURRENCY_CODE
    if instance.is_primary_exchange_rate_currency:
        primary_currency['exchange_rate_currency'] = instance.currency_code
    
    if instance.is_primary_store_currency:
        primary_currency['store_currency'] = instance.currency_code
    
    settings.PRIMARY_CURRENCY_CODE.update(primary_currency)

post_save.connect(set_primary_currency, sender=Currency)    
