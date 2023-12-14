import imp
from django.conf import settings
from apps.currency.format import FormatCurrency

def currency_formater():
    primary_currency = settings.PRIMARY_CURRENCY_CODE
    return FormatCurrency(primary_currency.get('exchange_rate_currency'))