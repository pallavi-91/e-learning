from django.contrib import admin
from .models import Country


# Register your models here.
@admin.register(Country)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name','sort_number','three_letter_iso_code','numeric_iso_code','allow_billing','date_updated',)
    search_fields = ('name','allow_billing',)