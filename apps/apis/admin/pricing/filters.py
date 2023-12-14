from django_filters import FilterSet, RangeFilter, rest_framework as filters
from rest_framework.filters import OrderingFilter,SearchFilter
from apps.courses.models import CoursePrice
import re
from apps.currency.models import Currency

class PriceTierFilter(FilterSet):
    price = RangeFilter()
    currency_name = filters.CharFilter(method='filter_by_currency_name', label='currency_name')
    class Meta:
        model = CoursePrice
        fields = ['price', 'currency', 'price_tier_status']
    #E.g. <your_api_endpoint>/?price_min=100&price_max=200
    
    def filter_by_currency_name(self, queryset, name, value):
        return queryset.filter(currency__name=value)

class CurrencyFilter(FilterSet):
    rate = RangeFilter()
    class Meta:
        model = Currency
        fields = ['rate', 'is_primary_exchange_rate_currency', 'is_primary_store_currency','pricing_tier_status',]
    #E.g. <your_api_endpoint>/?rate_min=100&rate_max=200
    
class PriceTierSearchFilter(SearchFilter):
    search_param = 'search'
    