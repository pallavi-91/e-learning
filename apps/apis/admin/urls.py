from django.urls import include, path
from rest_framework_simplejwt import views as jwt_views
from .pricing.controller import CurrencyView , PricingTierView
from .shares.controller import SharePricesView
from .countries.controller import CountryView
from .sales.urls import urlpatterns as sales_urls
from .courses.urls import urlpatterns as course_urls
from .users.urls import  urlpatterns as users_urls
from .geopricing.urls import urlpatterns as geopricing_list
from django.conf.urls import handler400, handler403, handler404, handler500
from rest_framework.exceptions import NotFound, APIException

def error404(request):
    raise NotFound(detail="Error 404, page not found", code=404)

def error500(request):
    raise APIException(detail="Something went wrong", code=500)

handler404 = error404
handler500 = error500

shares_list = [
        path('', SharePricesView.as_view({
            'get': 'list'
        })),
        path('create', SharePricesView.as_view({
            'post': 'create'
        })),
        path('<int:pk>', SharePricesView.as_view({
            'put': 'update',
        })),
    ]

currency_list = [
        path('', CurrencyView.as_view({
            'get': 'list',
        })),
        path('create', CurrencyView.as_view({
            'post': 'create'
        })),
        path('<int:pk>', CurrencyView.as_view({
            'put': 'partial_update',
            'delete':'destroy',
            'get': 'retrieve',
        })),
        path('code', CurrencyView.as_view({
            'get': 'currency_code',
        })),
        path('<int:pk>/currency-exchange', CurrencyView.as_view({
            'get': 'currency_exchange',
        })),
        path('live-rates', CurrencyView.as_view({
            'get': 'get_live_rates',
        })),
       
    ]

pricing_list = [
        path('', PricingTierView.as_view({
            'get': 'list'
        })),
        path('create', PricingTierView.as_view({
            'post': 'create'
        })),
        path('<int:pk>', PricingTierView.as_view({
            'put': 'update',
            'delete':'destroy',
            'get': 'retrieve',
        })),
        path('primary-currency', PricingTierView.as_view({
            'get': 'primary_currency'
        })),
        
    ]

countries_list = [
        path('', CountryView.as_view({
            'get': 'list'
        })),
        path('create', CountryView.as_view({
            'post': 'create'
        })),
        path('<int:pk>', CountryView.as_view({
            'put': 'update',
            'delete':'destroy',
            'get': 'retrieve',
        })),
        
    ]


urlpatterns = [
    path('token',jwt_views.TokenObtainPairView.as_view(),name ='token_obtain_pair'),
    path('token/refresh',jwt_views.TokenRefreshView.as_view(),name ='token_refresh'),
    path('shareprices/',include(shares_list)),
    path('currencies/',include(currency_list)),
    path('pricing/',include(pricing_list)),
    path('countries/',include(countries_list)),
    path('sales/',include(sales_urls)),
    path('courses/',include(course_urls)),
    path('users/',include(users_urls)),
    path('geopricing/',include(geopricing_list)),
]