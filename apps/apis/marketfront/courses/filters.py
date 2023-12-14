from time import timezone
from django_filters import rest_framework as filters
from apps.courses.models import Note, QnA
from apps.status import CourseStatus
from datetime import date, timedelta
from rest_framework.filters import OrderingFilter
from apps.utils.helpers import get_client_ip
from apps.courses.models import Category, Course, CourseView
from apps.users.models import UserClass
from django.db.models import Q, Count , Avg
from django.utils import timezone


# Equivalent FilterSet:
class CourseFilter(filters.FilterSet):
    VARIETY = (
        ('','Any'),
        ('trending','Trending'),
        ('recommended','Recommended'),
        ('popular','Popular'),
        ('newest','Newest'),
        ('highest_rated','Highest Rated'),
    )

    type = filters.CharFilter(method="type_filter", label='type')
    ratings = filters.CharFilter(method="ratings_filter", label='ratings')
    length = filters.CharFilter(method="length_filter", label='Video length')
    variety = filters.TypedChoiceFilter(method="variety_filter",choices=VARIETY, label='Variety')

    def variety_filter(self, queryset, name, value):
        is_auth = self.request.user.is_authenticated
        courses_purchased =  UserClass.objects.filter(user = self.request.user).values_list('course_id', flat=True).distinct()
        queryset  = queryset.exclude(id__in = courses_purchased)
        if value == 'popular':
            """Most popular """
            courses = CourseView.objects.filter(date_created__month=timezone.now().month)\
                .annotate(Count('course__id'))\
                .order_by()\
                .values_list('course__id',flat=True)
            return queryset.filter(id__in=courses)

        elif value == 'recommended':
                """filter course by topics"""
                q = Q(user=self.request.user) if is_auth else Q(ip=get_client_ip(self.request)) 
                views = CourseView.objects.select_related('course').prefetch_related('course__topics').filter(q)
                if views.exists():
                    view = views.latest('date_created')
                    return queryset.filter(topics__in=view.course.topics.values_list('id',flat=True))
                
        elif value == 'trending':
            """students are viwing """
            two_days_before = date.today() - timedelta(days=2)
            courses = CourseView.objects.filter(date_created__date__gte=two_days_before)\
                    .annotate(Count('course__id'))\
                    .order_by()\
                    .values_list('course__id',flat=True)
            return queryset.filter(id__in=courses)
        
        elif value == 'newest':
            """Newest Courses """
            return queryset.filter(status=CourseStatus.STATUS_PUBLISHED,is_deleted=False)\
                    .exclude(date_published=None).order_by('-date_published')
                    
        elif value == 'highest_rated':
            """Highest Rated Courses """
            return queryset.filter(status=CourseStatus.STATUS_PUBLISHED,is_deleted=False)\
                        .exclude(reviews__rate=None).annotate(avg_rating=Avg('reviews__rate')).order_by('-avg_rating')
        
        return queryset

    def type_filter(self, queryset, name, value):
        q = Q()
        for type in value.split(","):
            if type == 'free': q = q | Q(pricing__tier_level__lte=0) 
            elif type == 'paid': q = q | Q(pricing__tier_level__gt=0) 
        
        return queryset.filter(q)

    def length_filter(self, queryset, name, value):
        one_hour = 3600
        three_hours = one_hour * 3
        six_hours = one_hour * 6
        ten_hours = one_hour * 10 
        q = Q()
        for length in value.split(","):
            length = int(length)
            if length == 0: q = q | Q(id__in=[x.id for x in queryset if x.duration >= 0 and x.duration <= one_hour ])
            if length == 1: q = q | Q(id__in=[x.id for x in queryset if x.duration > one_hour and x.duration < three_hours ])
            if length == 3: q = q | Q(id__in=[x.id for x in queryset if x.duration > three_hours and x.duration < six_hours ])
            if length == 6: q = q | Q(id__in=[x.id for x in queryset if x.duration > six_hours and x.duration < ten_hours ])
            if length == 10: q = q | Q(id__in=[x.id for x in queryset if x.duration > ten_hours ])

        return queryset.filter(q)

    
    def ratings_filter(self, queryset, name, value):
        q = Q()
        for rate in value.split(","):
            rate = float(rate)
            q = q | Q(id__in=[x.id for x in queryset if x.total_rate >= round(rate) and x.total_rate <= rate])

        return queryset.filter(q)

    class Meta:
        model = Course
        fields = ['category','subcategory', 'subcategory__slug','category__slug','topics__slug','skill_level','language']



class CategoryFilter(filters.FilterSet):
    with_course = filters.BooleanFilter(method="with_course_filter", label='Has a course?')

    def with_course_filter(self, queryset, name, value):
        if value:
            return queryset.filter(courses__status=CourseStatus.STATUS_PUBLISHED,courses__is_deleted=False)\
                    .annotate(courses_count=Count('courses'))\
                    .exclude(courses_count=0)

        return queryset

    class Meta:
        model = Category
        fields = ['date_created']


class NotesFilter(filters.FilterSet):
    lecture = filters.CharFilter(method="lecture_filter", label='Lecture Subsection')
    class Meta:
        model = Note
        fields = ['type']
    

    def lecture_filter(self, queryset, name, value):
        if value != 'all':
            queryset = queryset.filter(subsection__id=value)
        return queryset
    
class QnAFilter(filters.FilterSet):
    QVARIETY = (
        ('','Any'),
        ('following','Im Following'),
        ('asked','I asked'),
        ('blank','Question with no response'),
    )

    lecture = filters.CharFilter(method="lecture_filter", label='Lecture Subsection')
    variety = filters.TypedChoiceFilter(method="variety_filter",choices=QVARIETY, label='Variety')
    upvoted = filters.CharFilter(method="upvoted_filter", label='Lecture upvoted')

    class Meta:
        model = QnA
        fields = ['approved']
    

    def lecture_filter(self, queryset, name, value):
        if value != 'all':
            queryset = queryset.filter(subsection__id=value)
        return queryset
    
    def variety_filter(self, queryset, name, value):

        if value == 'following':
            return queryset.prefetch_related('qnas').filter(qnas__user=self.request.user)
        elif value == 'asked':
            return queryset.filter(user=self.request.user)
        elif value == 'blank':
            return queryset.prefetch_related('qnas').annotate(total_reply=Count('qnas')).filter(total_reply=0)

        return queryset
    
    def upvoted_filter(self, queryset, name, value):
        if value:
            return queryset.annotate(upvoted_count=Count('upvoted_users')).order_by('-upvoted_count')
        return queryset


class QnaOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            # custom sorting logic
            return queryset.annotate(upvoted=Count('upvoted_users')).order_by(*ordering)

        return queryset