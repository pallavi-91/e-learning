from django.contrib import admin
from .models import Currency


# Register your models here.
@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'currency_code','rate', 'is_primary_exchange_rate_currency','is_primary_store_currency',
                    'pricing_tier_status', 'published',)
    search_fields = ('name','is_primary_exchange_rate_currency',)