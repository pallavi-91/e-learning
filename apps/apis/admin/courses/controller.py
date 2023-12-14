import arrow
from django.shortcuts import get_object_or_404
from apps.courses.models import Course , CourseType, CourseChangeHistory
from apps.transactions.models import Transactions, TransactionTypes
from apps.users.models import Order, UserClass
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.apis.admin.paginations import CommonPagination
from apps.utils.filters import IOrderingFilter
from .serializers import (
    CourseCategorySerializer,
    CourseChangeHistorySerializer,
    CoursePricingSerializer,
    CourseSerializer, 
    CourseStatisticsSerializer, 
    CourseDetailSerializer, 
    CourseSubCategorySerializer, 
    CourseTopicsSerializer, 
    SectionSerializer, 
    SubSectionSerializer, 
    CourseUserProgressSerializer, 
    UserCertificationSerializer, )
import arrow
from django.conf.global_settings import LANGUAGES
from django.db.models.functions import Coalesce
from django.db.models import Avg, Case, Count, F, Func, Max, Min, Prefetch, Q, Sum, When, FloatField, Value
from apps.status import CourseSkillLevel, CourseStatus
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter,SearchFilter
from .filters import CourseFilter, FeedbackCourseFilter
from apps.courses.models import Category, CourseView as CourseChecked, SubCategory, SubSection, Topic, QnA


class CourseView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CourseSerializer
    pagination_class = CommonPagination
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = CourseFilter
    lookup_field = 'code'
    queryset = Course.objects.select_related('user', 'category').prefetch_related('classes').all()
    search_fields = ['id', 'title', 'type','status']
    ordering_fields = ['title','date_published','pricing__tier_level','pricing__price']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def recently_updated(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        last_start = arrow.now().shift(days=-6)
        queryset = Course.objects.filter(Q(date_updated__date__gte=last_start.date()) & Q(date_updated__date__lte=current_start.date()))
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def statistic_overview(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(status = CourseStatus.STATUS_PUBLISHED))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CourseStatisticsSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)
        
        serializer = CourseStatisticsSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CourseDetailSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def section_list(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = instance.sections.prefetch_related('subsections').all()
        serializer = SectionSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def subsection_list(self, request, *args, **kwargs):
        course = self.get_object()
        instance = get_object_or_404(course.sections.all(), id= kwargs.get('section'))
        subsections = instance.subsections.select_related('assignment', 'quiz', 'lecture', 'section').prefetch_related('progress').all()
        serializer = SubSectionSerializer(subsections, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}
        serializer = CourseDetailSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def section_update(self, request, *args, **kwargs):
        section = get_object_or_404(SectionSerializer.Meta.model, **kwargs)
        serializer = SectionSerializer(instance=section, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)
    
    def subsection_delete(self, request, *args, **kwargs):
        course = self.get_object()
        sections = get_object_or_404(course.sections.all(), id= kwargs.get('section'))
        instance = get_object_or_404(sections.subsections.all(), id= kwargs.get('subsection'))
        instance.delete()
        return Response(status=204)
    
    def pricing_detail(self, request, *args, **kwargs):
        course = self.get_object()
        serializer = CoursePricingSerializer(instance=course.pricing)
        return Response(serializer.data)
    

class CourseStatisticView(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    queryset = Course.objects.select_related('user', 'category').prefetch_related('classes').filter(status = CourseStatus.STATUS_PUBLISHED)
    search_fields = ['id', 'title']
    
    def enrollments(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        days = request.GET.get('days', '10')
        last_start = arrow.now().shift(days=-int(days))
        data = Course.objects.values('date_updated__date').annotate(date = F('date_updated__date'),\
                                    paid_courses=Count('id', filter=Q(date_updated__date__gte=last_start.date())\
                                    & Q(date_updated__date__lte=current_start.date()) & Q(type = CourseType.PAID)),\
                                    free_courses=Count('id', filter=Q(date_updated__date__gte=last_start.date())\
                                    & Q(date_updated__date__lte=current_start.date()) & Q(type = CourseType.FREE)),\
                                    ).values('date','paid_courses','free_courses').order_by('date')
        return Response(data)
    
    # To Do based on top sales transaction in given days
    def top_courses(self, request, *args, **kwargs):
        days = request.GET.get('days', '10')
        from_date = arrow.now().shift(days=-int(days))
        queryset = self.get_queryset()
        queryset = queryset.prefetch_related('classes').annotate(sales=Count('classes__transactions', filter=
                                                                  Q(classes__transactions__type = TransactionTypes.SALE) & 
                                                                  Q(classes__transactions__date_updated__date__gte=from_date.date())))
        
        data = queryset.values('title', 'sales').order_by('-sales')[:5]
        return Response(data)
    

    def most_popular(self, request, *args, **kwargs):
        days = request.GET.get('days', '10')
        from_date = arrow.now().shift(days=-int(days))
        data = CourseChecked.objects.select_related('course')\
                .annotate(current_views = Count('course__id', filter=Q(date_created__date__gte=from_date.date())),
                          total_views = Count('course__id'), 
                          title=F('course__title'))\
                .order_by('-current_views')\
                .values('total_views', 'current_views', 'title')[:5]
        
        return Response(data)
    
    def most_engaging(self, request, *args, **kwargs):
        days = request.GET.get('days', '7')
        from_date = arrow.now().shift(days=-int(days))
        queryset = self.get_queryset()
        queryset = queryset.prefetch_related('classes').annotate(sales=Count('classes__transactions', filter=
                                                                  Q(classes__transactions__type = TransactionTypes.SALE) & 
                                                                  Q(classes__transactions__date_updated__date__gte=from_date.date())),
                                                                 completed_course=Count('classes',filter=Q(classes__subsections__progress__is_completed=True)),
                                                                 fav_course=Count('favorites')).order_by('-completed_course', '-sales', '-fav_course')
        
        data = queryset.values('sales', 'completed_course', 'title', 'fav_course')[:5]
        return Response(data)
    
    def unfinished(self, request, *args, **kwargs):
        days = request.GET.get('days', '7')
        last_start = arrow.now().shift(days=-int(days))
        last_end = arrow.now().shift(days=-2)
        queryset = self.get_queryset()
        dataset = queryset.filter(date_created__date__lt=last_start.date()).annotate(
            total_lecture = Count('classes__subsections', filter=Q(classes__subsections__type=SubSection.LECTURE)),  
            completed_lecture = Count('classes__subsections__progress', filter=Q(classes__subsections__progress__is_completed=False) &
                                      Q(classes__subsections__progress__date_created=last_end.date())
                ), 
        ).values('total_lecture', 'completed_lecture', 'title').order_by('-completed_lecture')
        data = filter(lambda res: res.get('total_lecture') != res.get('completed_lecture'), dataset)
        return Response(list(data))
    

    def withdrawn(self, request, *args, **kwargs):
        days = request.GET.get('days', '7')
        last_start = arrow.now().shift(days=-int(days))
        queryset = self.get_queryset()
        
        queryset = queryset.filter(date_created__date__lt=last_start.date()).prefetch_related('classes').annotate(
            sales=Count('classes'),
            withdrawn=Count('classes__transactions', filter=Q(classes__transactions__refund=True))).order_by('-withdrawn')
        data = queryset.values('withdrawn', 'sales', 'title').order_by('-withdrawn')[:5]
        return Response(data)


class CourseExtrasView(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    
    def topic_list(self, request, *args, **kwargs):
        queryset = Topic.objects.all()
        serializer = CourseTopicsSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def category_list(self, request, *args, **kwargs):
        queryset = Category.objects.all()
        serializer = CourseCategorySerializer(queryset, many=True)
        return Response(serializer.data)
    
    def subcategory_list(self, request, *args, **kwargs):
        queryset = SubCategory.objects.all()
        serializer = CourseSubCategorySerializer(queryset, many=True)
        return Response(serializer.data)
    
    def language_list(self, request, *args, **kwargs):
        data = [dict(zip(('id', 'name'), i)) for i in LANGUAGES]
        return Response(data)


class CourseChangeHistoryView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CourseChangeHistorySerializer
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = FeedbackCourseFilter
    queryset = CourseChangeHistory.objects.select_related('user', 'course').all()
    search_fields = ['id', 'type','message',]
    ordering_fields = ['id','date_created',]
    

    def get_queryset(self):
        return super().get_queryset().filter(**self.kwargs)

    def create(self, request, *args, **kwargs):
        course = get_object_or_404(Course, code=kwargs.get('course__code'))
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course, user=request.user)
        return Response(serializer.data, status=201)
    
    def restore(self, request, *args, **kwargs):
        feedback_history = self.get_object()
        feedback_history.restore_version(request.user)
        return Response(status=204)
    
    def purge_all(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset.delete()
        return Response(status=204)
    
    def field_feedbacks(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=201)
    
    
class CourseDetailStatisticView(viewsets.GenericViewSet):
    permission_classes = [IsAdminUser]
    pagination_class = CommonPagination
    queryset = UserClass.objects.all()
    
    def users_progress(self, request, *args, **kwargs):
        course = get_object_or_404(Course, code=kwargs.get('code'))
        queryset = UserClass.objects.filter(course = course)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CourseUserProgressSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = CourseUserProgressSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def certifications(self, request, *args, **kwargs):
        course = get_object_or_404(Course, code=kwargs.get('code'))
        queryset = UserClass.objects.filter(course=course).exclude(Q(certificate='')|Q(certificate=None))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = UserCertificationSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserCertificationSerializer(queryset, many=True)
        return Response(serializer.data)  
    
    def general_stats(self, request, *args, **kwargs):
        course = get_object_or_404(Course, code=kwargs.get('code'))
        seven_date = arrow.now().shift(days=-6)
        active_date = arrow.now().shift(days=-2)
        context = UserClass.objects.select_related('user', 'course').filter(course=course).aggregate(
            total_users = Count('user', distinct=True),
            new_users = Count('user', distinct=True, filter=Q(date_updated__date__gte=seven_date.date())),
            active_users = Count('user', distinct=True, filter=Q(user__viewed_courses__date_updated__date__gte=active_date.date())),
            total_sales = Count('id', distinct=True, filter=Q(is_purchased=True)),
        )
        context['course_gross_revenue'] = course.course_gross_revenue
        context['duration'] = course.duration
        context['median_completion_times'] = course.median_completion_times
        return Response(context)  

    def sales_revenue(self, request, *args, **kwargs):
        context = {}
        course = get_object_or_404(Course, code=kwargs.get('code'))
        current_currency = course.currency_code
        filter_date = arrow.now().shift(days=-int(request.GET.get('days', '7')))
        queryset = UserClass.objects.filter(course = course, is_purchased=True, date_updated__date__gte=filter_date.date())
        for cls in queryset.iterator():
            date = cls.date_updated.strftime('%Y-%m-%d')
            price = cls.currency.exchange.convert(cls.price, cls.currency_code, current_currency) if cls.currency_code != current_currency else cls.price
            if date in context:
                context[date]['sales'] += 1
                context[date]['revenue'] += price
            else:
                context[date] = {
                    'sales': 1,
                    'revenue': price
                }
        return Response(context) 
