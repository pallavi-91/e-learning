from django_filters import rest_framework as filters
from apps.users.models import UserClass
from django.db.models import Q, Count


class UserClassFilter(filters.FilterSet):
    progress = filters.CharFilter(method="progress_filter", label='progress')
    instructor = filters.CharFilter(method="instructor_filter",label="instructor")
    category = filters.Filter(method="category_filter",label="category")
    class Meta:
        model = UserClass
        fields = ['code','course','subsections','currency','price','order','is_purchased', 'archived']

    def progress_filter(self,queryset,name,value):
        if value=="in_progress":
            return queryset.prefetch_related('subsections','subsections__progress').filter(Q(subsections__progress__user=self.request.user) & Q(subsections__progress__is_completed=False))
        elif value=="completed":
            return queryset.prefetch_related('subsections','subsections__progress').filter(Q(subsections__progress__user=self.request.user) & Q(subsections__progress__is_completed=True))
        return queryset
    
    def instructor_filter(self,queryset,name,value):
        if value:
            return queryset.filter(Q(course__user_id=value))
        return queryset
    
    def category_filter(self,queryset,name,value):
        if value:
            return queryset.filter(course__category_id=value)
        return queryset