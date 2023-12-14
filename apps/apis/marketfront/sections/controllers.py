from django.shortcuts import get_object_or_404

from django.utils.translation import gettext as _
from django.db import transaction
from django.db.models import Count 

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework.viewsets import ViewSet, GenericViewSet, ModelViewSet
from apps.courses.models import Lecture, SubSection
from apps.courses.paginations import SectionPagination, SubsectionPagination
from rest_framework import status
from apps.utils.query import SerializerProperty
from apps.utils.paginations import CursorViewSetPagination, ViewSetPagination
from django.db.models import Avg, Case, Count, F, Sum, When, FloatField, Value, Q, Max
from apps.apis.marketfront.courses.serializers import CourseSerializer

from .serializers import (
    ClassSectionSerializer,
    LectureDetailSerializer,
    SectionSerializer,
    LectureSerializer,
    LectureResourceSerializer,
    ShortLectureSerializer,
    SubSectionSerializer,
    SubsectionPositionSerializer,
    PublicSectionSerializer,
)


class PublicSections(SerializerProperty, ViewSetPagination , GenericViewSet):
    """ course section (public)
    """
    serializer_class = PublicSectionSerializer
    pagination_class = SectionPagination
    authentication_classes = ()
    permission_classes = (AllowAny,)

    def course_sections(self, request, **kwargs):
        pages = self.paginate_queryset(self._model.objects.prefetch_related('subsections', 'subsections__lecture').filter(**kwargs))
        serializer = self.get_serializer(pages, many=True)

        return self.get_paginated_response(serializer.data)
    
class SectionsView(SerializerProperty, ViewSetPagination , GenericViewSet):
    """ course section
    """
    serializer_class = SectionSerializer
    pagination_class = SectionPagination

    def create(self, request, **kwargs):
        course = get_object_or_404(
            CourseSerializer.Meta.model,
            code=kwargs.get('course__code')
        )
        if not course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(course=course)

        return Response(serializer.data, status=201)

    def update(self, request, **kwargs):
        section = get_object_or_404(self._model, **kwargs)
        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.serializer_class(
            data=request.data,
            instance=section
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=200)

    def delete(self, request, **kwargs):
        section = get_object_or_404(self._model, **kwargs)

        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        section.delete()

        return Response(status=204)

    def get(self, request, **kwargs):
        serializer = self.get_serializer(
            get_object_or_404(self._model, **kwargs))
        return Response(serializer.data, status=200)

    def list(self, request, **kwargs):
        queryset = self._model.objects.prefetch_related('subsections').filter(**kwargs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def class_section(self,request,**kwargs):
        queryset = self._model.objects.prefetch_related('subsections').filter(**kwargs)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ClassSectionSerializer(page, many=True, context = self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ClassSectionSerializer(queryset, many=True, context = self.get_serializer_context())
        return Response(serializer.data)
    

class LecturesView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ lecture content
    """
    serializer_class = LectureSerializer
    pagination_class = SectionPagination
    queryset = Lecture.objects.prefetch_related('resources')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = LectureDetailSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data)
    
    def create(self, request):
        
        section = get_object_or_404(
            SectionSerializer.Meta.model, **request.query_params.dict())

        if not section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = self.serializer_class(
            data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(section=section)

        return Response(serializer.data, status=201)

    def update(self, request, **kwargs):
        lecture = get_object_or_404(self._model, **kwargs)

        if not lecture.section.course.is_editable:
            raise exceptions.PermissionDenied()
        
        serializer = self.serializer_class(
            data=request.data,
            instance=lecture,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=200)

    def delete(self, request, **kwargs):
        lecture = get_object_or_404(self._model, **kwargs)

        if not lecture.section.course.is_editable:
            raise exceptions.PermissionDenied()

        lecture.delete()

        return Response(status=204)

    def list(self, request):
        queryset = self._model.objects.filter(**request.query_params.dict()).order_by('id')
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    def short_list(self,request,**kwargs):
        serializer = ShortLectureSerializer(
            self._model.objects.filter(section__id=kwargs.get('id')),
            context=self.get_serializer_context(),
            many=True
        )
        return Response(serializer.data)


class SubSectionView(SerializerProperty, CursorViewSetPagination, GenericViewSet):
    
    serializer_class = SubSectionSerializer
    pagination_class = SubsectionPagination

    def get_subsection_class(self,request,**kwargs):
        """ get the subsection by section id on view course """
        section = get_object_or_404(
            SectionSerializer.Meta.model.objects.all(),
            **kwargs)
        qs = section.subsections.all()
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page,many=True)
        return self.get_paginated_response(serializer.data)

    def delete(self,request,**kwargs):
        sub_section = get_object_or_404(
            self._model.objects.all(),
            section__course__user=request.user,
            **kwargs)

        if not sub_section.section.course.is_editable:
            raise exceptions.PermissionDenied()
        
        sub_section.delete()
        return Response()
        
    def get_subsection_list(self,request,**kwargs):
        section = get_object_or_404(
            SectionSerializer.Meta.model.objects.all(),
            course__user=request.user,
            **kwargs)
        queryset = self.filter_queryset(section.subsections.all())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @transaction.atomic
    def update_subsection_position(self,request,**kwargs):
        serializer = SubsectionPositionSerializer(many=True,data=request.data.get("data"))
        serializer.is_valid(raise_exception=True)

        for data in serializer.validated_data:
            subsection = data.get("subsection")

            if not subsection.section.course.is_editable:
                raise exceptions.PermissionDenied()

            position = data.get("position")
            subsection.position = position
            subsection.save()
            
        return Response(serializer.data)

    @transaction.atomic
    def create_lecture(self,request,**kwargs):
        section = get_object_or_404(
            SectionSerializer.Meta.model,
            course__user=request.user, 
            **kwargs)

        if not section.course.is_editable:
            raise exceptions.PermissionDenied()
            
        serializer = LectureSerializer( 
            context=self.get_serializer_context(),
            data=request.data)
        serializer.is_valid(raise_exception=True)
        lecture = serializer.save(section=section)
        subs = SubSection.objects.create(
            type=SubSection.LECTURE,
            lecture=lecture,
            section=section
        )
        return Response(self.get_serializer(subs).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update_lecture(self,request,**kwargs):
        subsection = get_object_or_404(self._model,section__course__user=request.user, **kwargs)
        
        if not subsection.section.course.is_editable:
            raise exceptions.PermissionDenied()

        serializer = LectureSerializer(
                instance=subsection.lecture,
                data=request.data,
                partial=True,
                context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(self.get_serializer(subsection).data)


    

    
class LectureResources(SerializerProperty, ViewSet):
    """ lecture resources
    """
    serializer_class = LectureResourceSerializer

    def create(self, request, **kwargs):
        lecture = get_object_or_404(LectureSerializer.Meta.model, **kwargs)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(lecture=lecture)

        return Response(serializer.data, status=201)

    def delete(self, request, **kwargs):
        resource = get_object_or_404(self._model, **kwargs)
        resource.delete()

        return Response(status=204)

    def list(self, request, **kwargs):
        serializer = self.serializer_class(
            self._model.objects.filter(lecture__id=kwargs.get('id')),
            many=True
        )
        return Response(serializer.data, status=200)

