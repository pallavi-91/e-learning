from django.urls import path

from .controllers import CountryResourceView

urlpatterns = [
    path('countries/', CountryResourceView.as_view({
        'get': 'list',
    })),
]
