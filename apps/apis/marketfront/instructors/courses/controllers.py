from django.shortcuts import get_object_or_404
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from django_filters import rest_framework as filters
from apps.apis.admin.courses.filters import FeedbackCourseFilter
from apps.courses.models.change_history import CourseChangeHistory
from apps.utils.filters import IOrderingFilter
from django.db.models import Avg, Case, Count, F, Sum, When, FloatField, Value, Q, Max
from django.db.models.functions import Coalesce, Round
from .serializers import CourseChangeHistorySerializer, InstructorCourseSerializer, InstructorCourseDetailSerializer, CurrencySerializer, PricingTierSerializer
from rest_framework import viewsets
from apps.status import CourseStatus
from apps.courses.models import Course, CoursePrice
from rest_framework.response import Response
from rest_framework import status
from apps.apis.marketfront.paginations import CommonPagination
from apps.currency.models import Currency

class InstructorCourseView(viewsets.ModelViewSet):
    serializer_class = InstructorCourseSerializer
    pagination_class = CommonPagination
    filter_backends = [OrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_fields = ['category', 'subcategory','status']
    ordering_fields = ['title','date_updated']
    queryset = Course.objects.all()
    
    def get_queryset(self):
        return super().get_queryset().filter(user = self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = InstructorCourseDetailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), **kwargs)
        if instance.classes.count() != 0:
            raise Exception('Course cannot be deleted.')
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def update(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), **kwargs)
        serializer = InstructorCourseDetailSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), **kwargs)
        serializer = InstructorCourseDetailSerializer(instance)
        return Response(serializer.data)
    
    def currency_list(self, request, *args, **kwargs):
        queryset = Currency.objects.all()
        serializer = CurrencySerializer(queryset, many=True)
        return Response(serializer.data)
    
    def pricing_tier_list(self, request, *args, **kwargs):
        queryset = CoursePrice.objects.all()
        serializer = PricingTierSerializer(queryset, many=True)
        return Response(serializer.data)

    def submit_for_review(self,request,**kwargs):
        course = get_object_or_404(self.get_queryset(), **kwargs)
        if course.status not in [CourseStatus.STATUS_DRAFT, CourseStatus.STATUS_REJECTED]:
            return Response({})

        if course.is_valid_for_review:
            course.status = CourseStatus.STATUS_INREVIEW
            course.save()
            return Response({})
        return Response(course.needed_for_review)

class CourseChangeHistoryView(viewsets.ModelViewSet):
    serializer_class = CourseChangeHistorySerializer
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = FeedbackCourseFilter
    queryset = CourseChangeHistory.objects.select_related('user', 'course').all()
    search_fields = ['id', 'type','message',]
    ordering_fields = ['id','date_created',]
    
    def get_queryset(self):
        return super().get_queryset().filter(**self.kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(course__user=request.user))
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)