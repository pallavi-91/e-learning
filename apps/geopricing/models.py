from django.db import models
from apps.status.mixins import AtMostOneBooleanField, AutoCreatedUpdatedMixin
from apps.currency.models import Currency
from apps.countries.models import Country
from apps.courses.models import CoursePrice
from decimal import Decimal
# from django.core.validators import MinValueValidator, MaxValueValidator
        
# PERCENTAGE_VALIDATOR = [MinValueValidator(-100), MaxValueValidator(100)]

class GeoLocations(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = "geo_locations"
        ordering = ['-id']
        constraints = [
            models.UniqueConstraint(fields=['country', 'currency'], name='geolocation_country_currency_constraint_unique')
        ]
        
    country = models.ForeignKey(Country,related_name="countries", on_delete=models.CASCADE)
    currency = models.ForeignKey(Currency,related_name="currencies", on_delete=models.CASCADE)
    status = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"<Geo Location> {self.country} {self.currency}"
    
        
class GeoPricing(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = "geo_pricing"
        ordering = ['-id']
        
    geo_location = models.OneToOneField(GeoLocations,related_name="geo_pricing", on_delete=models.CASCADE)
    currency_convert = models.BooleanField(default=True)
    status = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"<Geo Pricing> {self.id}"
    
class GeoPricingTiers(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = "geo_pricing_tiers"
        ordering = ['-id']
        
    pricing_tier = models.ForeignKey(CoursePrice,related_name="geo_pricing_tier_course", on_delete=models.CASCADE)
    geo_pricing = models.ForeignKey(GeoPricing,related_name="geo_pricing_tier", on_delete=models.CASCADE)
    percentage = models.FloatField(default=0)
    is_deleted = models.BooleanField(default=False)
    
    def __str__(self) -> str:
        return f"<Geo Pricing Tier> {self.id}"