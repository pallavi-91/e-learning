from django.urls import include, path
from .controller import GeoLocationView


geolocation_urls = [
    path('', GeoLocationView.as_view({
        'get': 'list',
        'post':'create'
    })),
    path('<int:pk>', GeoLocationView.as_view({
        'get': 'retrieve',
        'put':'update',
        'delete':'destroy'
    })),
    path('<int:pk>/geo-pricing-tiers', GeoLocationView.as_view({
        'get': 'geo_pricing_tiers',
    })),
    path('<int:pk>/update-geopricing', GeoLocationView.as_view({
        'put': 'update_geopricing',
    }))
]
urlpatterns = [
    path('geolocations/', include(geolocation_urls)),
]