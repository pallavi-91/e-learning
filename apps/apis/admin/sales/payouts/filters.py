from django_filters import rest_framework as filters
from apps.transactions.models import InstructorPayouts

class PayoutsFilter(filters.FilterSet):
    type = filters.CharFilter(method="type_filter", label='type')
    class Meta:
        model = InstructorPayouts
        fields = ['status', 'period', 'user']
        
    def type_filter(self, queryset, name, value):
        if value:
            return queryset.filter(payout_type=value)
        return queryset

    
