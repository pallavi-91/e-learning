from django.urls import include, path
from .admin.urls import urlpatterns as adminurls
from .marketfront.urls import urlpatterns as marketplaceurls

urlpatterns = [
    path('admin/',include(adminurls)),
    path('marketplace/',include(marketplaceurls))
]