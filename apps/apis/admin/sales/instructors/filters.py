from dataclasses import dataclass, asdict
from django_filters import FilterSet, RangeFilter, rest_framework as filters
from django_filters import DateFromToRangeFilter
from rest_framework.filters import OrderingFilter,SearchFilter
from apps.statements.models import Statement
from apps.users.models import Instructor
from django.db.models import Q

class InstructorFilter(FilterSet):
    account_status = filters.BooleanFilter(method='filter_status', label='account_status')
    instructor_name = filters.CharFilter(method='filter_instructor_name', label='instructor_name')
    class Meta:
        model = Instructor
        fields = ['account_status', 'instructor_name']
    
    def filter_status(self, queryset, name, value):
        return queryset.filter(user__is_active=value)
    
    def filter_instructor_name(self, queryset, name, value):
        return queryset.filter(Q(user__first_name__istartswith=value)|Q(user__last_name__istartswith=value))

class InstructorSearchFilter(SearchFilter):
    search_param = 'search'
        
@dataclass
class CountByDate():
    total_instructors: int = 0
    instructor_increase_from_last_month: float = 0
    total_orders: int = 0
    order_increase_from_last_month: float = 0
    