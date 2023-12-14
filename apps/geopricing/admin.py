from django.contrib import admin
from .models import GeoLocations, GeoPricing, GeoPricingTiers


# Register your models here.
@admin.register(GeoLocations)
class GeoLocationsAdmin(admin.ModelAdmin):
    list_display =('country','currency')
    search_fields = ('country','currency',)
    
@admin.register(GeoPricing)
class GeoPricingAdmin(admin.ModelAdmin):
    list_display =('geo_location','currency_convert','status')
    search_fields = ('geo_location','currency_convert',)
    
@admin.register(GeoPricingTiers)
class GeoPricingTiersAdmin(admin.ModelAdmin):
    list_display =('geo_pricing','pricing_tier','percentage')
    search_fields = ('geo_pricing','pricing_tier',)

