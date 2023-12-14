from time import timezone
from django_filters import rest_framework as filters
from apps.courses.models.change_history import CourseChangeHistory
from apps.status import CourseStatus
from apps.utils.helpers import get_client_ip
from apps.courses.models import Course
from django.db.models import Q, Count
from datetime import date, timedelta
from apps.courses.models import CourseView, SubSection


# Equivalent FilterSet:
class CourseFilter(filters.FilterSet):
    VARIETY = (
        ('','Any'),
        ('trending','Trending'),
        ('popular','Popular'),
        ('unfinished','Unfinished'),
        ('withdrawn','Withdrawn'),
    )
    
    type = filters.CharFilter(method="get_type_filter", label='Course type')
    ratings = filters.CharFilter(method="get_ratings_filter", label='Course ratings')
    length = filters.CharFilter(method="get_length_filter", label='Video length')
    resource_mode = filters.CharFilter(method="get_lectures_type_filter", label='Lecture Type')
    course_sold = filters.CharFilter(method="get_course_sold_filter", label='Solded courses')
    sale_price = filters.CharFilter(method="get_sale_price_filter", label='Sale Price')
    sections = filters.CharFilter(method="get_sections_filter", label='Sections')
    lectures = filters.CharFilter(method="get_lectures_filter", label='Lectures')
    variety = filters.TypedChoiceFilter(method="variety_filter",choices=VARIETY, label='Variety')
    
    def variety_filter(self, queryset, name, value):

        if value == 'popular':
            """Most popular """
            courses = CourseView.objects.filter(date_created__month=timezone.now().month)\
                .annotate(Count('course__id'))\
                .order_by()\
                .values_list('course__id',flat=True)
            return queryset.filter(id__in=courses)
                
        elif value == 'trending':
            """Most engaging courses """
            two_days_before = date.today() - timedelta(days=2)
            courses = CourseView.objects.filter(date_created__date__gte=two_days_before)\
                    .annotate(Count('course__id'))\
                    .order_by()\
                    .values_list('course__id',flat=True)
            return queryset.filter(id__in=courses)
        
        elif value == 'unfinished':
            """Unfinished Courses """
            ids = set()
            two_days_before = date.today() - timedelta(days=2)
            for course in queryset.iterator():
                res = course.classes.filter(date_created__date__lt=two_days_before).select_related('subsections').aggregate(
                    total_lecture = Count('subsections', filter=Q(subsections__type=SubSection.LECTURE)),
                    completed_lecture = Count('subsections__progress', filter=Q(subsections__progress__is_completed=False)),
                )
                if res.get('total_lecture') != res.get('completed_lecture'):
                    ids.add(course.id)
            
            return queryset.filter(id__in=ids)
                    
        elif value == 'withdrawn':
            """Withdrawn Courses """
            
            return queryset.prefetch_related('classes').annotate(refunded=Count('classes__transactions', filter=Q(classes__transactions__refund=True))).order_by('-refunded')
        
        return queryset
    
    def get_sale_price_filter(self, queryset, name, value):
        min_value, max_value = value.split(',')
        queryset = queryset.select_related('pricing').filter(pricing__price__gte=min_value, pricing__price__lte=max_value)
        return queryset
    
    def get_course_sold_filter(self, queryset, name, value):
        min_value, max_value = value.split(',')
        queryset = queryset.prefetch_related('classes').annotate(sold_course=Count('classes')).filter(sold_course__gte=min_value, sold_course__lte=max_value)
        return queryset
    
    def get_lectures_filter(self, queryset, name, value):
        min_value, max_value = value.split(',')
        queryset = queryset.prefetch_related('sections').annotate(total_lectures=Count('sections__subsections__id', filter=Q(sections__subsections__type=SubSection.LECTURE)))
        return queryset.filter(total_lectures__gte=min_value, total_lectures__lte=max_value)
    
    def get_sections_filter(self, queryset, name, value):
        min_value, max_value = value.split(',')
        queryset = queryset.prefetch_related('sections').annotate(total_sections=Count('id'))
        return queryset.filter(total_sections__gte=min_value, total_sections__lte=max_value)
    
    def get_lectures_type_filter(self, queryset, name, value):
        q = Q()
        for mode in value.split(","):
            q = q | Q(id__in=[course.id for course in queryset.iterator() if course.resource_mode == mode ])
            
        return queryset.filter(q)

    def get_type_filter(self, queryset, name, value):
        q = Q()
        for type in value.split(","):
            if type == 'free': q = q | Q(pricing__tier_level__lte=0) 
            elif type == 'paid': q = q | Q(pricing__tier_level__gt=0) 
        
        return queryset.filter(q)

    def get_length_filter(self, queryset, name, value):
        one_hour = 3600
        three_hours = one_hour * 3
        six_hours = one_hour * 6
        ten_hours = one_hour * 10 
        q = Q()
        for length in value.split(","):
            length = int(length)
            if length == 0: q = q | Q(id__in=[x.id for x in queryset if x.duration >= 0 and x.duration < one_hour ])
            if length == 1: q = q | Q(id__in=[x.id for x in queryset if x.duration > one_hour and x.duration < three_hours ])
            if length == 3: q = q | Q(id__in=[x.id for x in queryset if x.duration > three_hours and x.duration < six_hours ])
            if length == 6: q = q | Q(id__in=[x.id for x in queryset if x.duration > six_hours and x.duration < ten_hours ])
            if length == 10: q = q | Q(id__in=[x.id for x in queryset if x.duration > ten_hours ])

        return queryset.filter(q)

    
    def get_ratings_filter(self, queryset, name, value):
        q = Q()
        for rate in value.split(","):
            rate = int(rate)
            if rate == 5: q = q | Q(id__in=[x.id for x in queryset if x.total_rate == 5])
            if rate == 4: q = q | Q(id__in=[x.id for x in queryset if x.total_rate >= 4])
            if rate == 3: q = q | Q(id__in=[x.id for x in queryset if x.total_rate >= 3])
            if rate == 2: q = q | Q(id__in=[x.id for x in queryset if x.total_rate >= 2])

        return queryset.filter(q)

    class Meta:
        model = Course
        fields = ['category','subcategory', 'status', 'type', 'skill_level','language']


class FeedbackCourseFilter(filters.FilterSet):

    class Meta:
        model = CourseChangeHistory
        fields = ['type', 'section', 'lecture', 'quiz', 'assignment_question', 'pricing', 'assignment', 'quiz_question', 'intended_learners', 'pricing',]