from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from apps.courses.paginations import ClassPagination, SubsectionProgressPagination
from django_filters import rest_framework as filters
from apps.users.models.classes import UserClass
from apps.users.tasks import class_generate_certificate
from apps.utils.filters import IOrderingFilter
from apps.utils.query import SerializerProperty
from apps.utils.paginations import ViewSetPagination
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from .serializers import ClassSectionSerializer, ClassSerializer, ClassSubsectionSerializer, ShortClassSerializer, SubsectionProgressSerializer, ToggleCompleteSerializer
from rest_framework.filters import OrderingFilter,SearchFilter
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from apps.courses.models import Section
from .filters import UserClassFilter

class ClassesView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ user classes
    """
    serializer_class = ClassSerializer
    pagination_class = ClassPagination
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class = UserClassFilter
    ordering_fields = ['date_created','course__title','course__subtitle','date_updated']
    search_fields = ['course__title','course__subtitle']
    
    def get_queryset(self, *args, **kwargs):
        return self.request.user.user_classes.select_related('course', 'user').prefetch_related('subsections').filter(is_purchased=True)
    
    # @method_decorator(cache_page(60*2, key_prefix='classes-list'))
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        
        return self.get_paginated_response(serializer.data)

    def get_class_by_code(self,request,**kwargs):
        user_class = get_object_or_404(
            self.get_queryset(),
            code=kwargs.get('code')
        )
        return Response(self.get_serializer(user_class).data)


    def toggle_complete(self,request, **kwargs):    
        user_class = get_object_or_404(
            self.get_queryset(),
            **kwargs
        )
        serializer = ToggleCompleteSerializer(
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.toggle(user_class)
        return Response()

    def get_sections(self, request, *args, **kwargs):
        user_class = get_object_or_404(
            self.get_queryset(),
            code=kwargs.get('code')
        )
        sections = user_class.course.sections.distinct()
        serializer = ClassSectionSerializer(sections, context=self.get_serializer_context(), many=True)
        return Response(serializer.data)
    
    def toggle_archive(self,request,**kwargs):
        """Toggle course for archive"""
        user_class = get_object_or_404(self.get_queryset(),**kwargs)
        user_class.archived = not user_class.archived 
        user_class.save()
            
        serializer = self.get_serializer(user_class)
        return Response(data=serializer.data, status=201)

class SubsectionProgressView(SerializerProperty, ViewSetPagination, ModelViewSet):
    
    serializer_class = SubsectionProgressSerializer
    pagination_class = SubsectionProgressPagination
    filter_backends = (SearchFilter, OrderingFilter,)
    ordering_fields = ['date_created','date_updated']

    def get_queryset(self):
        return self._model.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user,**self.kwargs)


    def update_or_create(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.update_or_create()
        return Response(serializer.data)

class CourseCertificationView(SerializerProperty, ViewSetPagination, GenericViewSet):
    serializer_class = ShortClassSerializer

    def get_object(self):
        return get_object_or_404(UserClass, **self.kwargs)
    
    def course_progress(self,request, *args, **kwargs):
        instance = self.get_object()
        context = dict()
        result = request.user.class_progress.filter(subsection__section__course=instance.course).aggregate(progress=Count('id', filter=Q(is_completed=True)))
        subsection_total = instance.course.sections.prefetch_related('subsections').aggregate(total=Count('subsections'))
        context['course_progress'] =  round((result.get('progress') / (subsection_total.get('total') or 1)) * 100)
        if context['course_progress'] == 100:
            # If curse completed then trigger generate certificate
            class_generate_certificate(instance)
        return Response(context)
    
    def course_overview(self,request, *args, **kwargs):
        course = self.get_object()
        serializer = ShortClassSerializer(instance = course)
        return Response(serializer.data)
    