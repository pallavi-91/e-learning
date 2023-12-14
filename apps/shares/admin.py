from django.contrib import admin
from .models import SharePrices


# Register your models here.
@admin.register(SharePrices)
class SharePricesAdmin(admin.ModelAdmin):
    list_display = ('share_types', 'instructor_share','platform_share', 'date_updated')
    search_fields = ('share_types',)
    