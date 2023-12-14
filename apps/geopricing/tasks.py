from huey.contrib.djhuey import db_periodic_task, db_task
from huey import crontab
from .models import GeoLocations, GeoPricing, GeoPricingTiers
from apps.courses.models import CoursePrice

@db_task(name="create_geo_pricing")
def create_geo_pricing(geolocation_id=None):
    geopricing = GeoPricing.objects.create(geo_location_id=geolocation_id)
    pricing_tiers = CoursePrice.objects.all()  # filter required for status ?
    create_gopricing_tiers = []
    for pricing_tier in pricing_tiers:
        create_gopricing_tiers.append(GeoPricingTiers(pricing_tier = pricing_tier, geo_pricing_id = geopricing.id)) 
    GeoPricingTiers.objects.bulk_create(create_gopricing_tiers, update_conflicts = False) 