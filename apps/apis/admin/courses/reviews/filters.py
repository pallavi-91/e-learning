from django_filters import rest_framework as filters
from apps.courses.models import CourseReview
from django.db.models import Q


# Equivalent FilterSet:
class CourseReviewFilter(filters.FilterSet):
    rate = filters.CharFilter(lookup_expr='icontains', label='Rate')
    

    class Meta:
        model = CourseReview
        fields = ['user','course', ]
