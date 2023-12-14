from django.shortcuts import get_object_or_404
from apps.courses.models import Course 
from rest_framework import viewsets
from rest_framework import parsers, status
from rest_framework.response import Response
from .serializers import (
    CourseIntendedObjectives, 
    CourseIntendedLearners,
    CourseIntendedRequirements,)

class CourseObjectivesView(viewsets.ModelViewSet):
    serializer_class = CourseIntendedObjectives
    queryset = CourseIntendedObjectives.Meta.model.objects.all()
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        return super().get_queryset().filter(course__id=self.kwargs.get('course_id'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
   
    def create(self, request, *args, **kwargs):
        queryset = self.perform_update_or_create(request.data)
        serialized_queryset = self.get_serializer(queryset, many=True)
        return Response(serialized_queryset.data, status=status.HTTP_200_OK)
    
    def perform_update_or_create(self, validated_data):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer = self.get_serializer()
        queryset = serializer.update_or_create(validated_data, course)
        return queryset
    

class CourseLearnersView(viewsets.ModelViewSet):
    serializer_class = CourseIntendedLearners
    queryset = CourseIntendedLearners.Meta.model.objects.all()
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        return super().get_queryset().filter(course__id=self.kwargs.get('course_id'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        queryset = self.perform_update_or_create(request.data)
        serialized_queryset = self.get_serializer(queryset, many=True)
        return Response(serialized_queryset.data, status=status.HTTP_200_OK)
    
    def perform_update_or_create(self, validated_data):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer = self.get_serializer()
        queryset = serializer.update_or_create(validated_data, course)
        return queryset

class CourseRequirementView(viewsets.ModelViewSet):
    serializer_class = CourseIntendedRequirements
    queryset = CourseIntendedRequirements.Meta.model.objects.all()
    parser_classes = [parsers.JSONParser]

    def get_queryset(self):
        return super().get_queryset().filter(course__id=self.kwargs.get('course_id'))

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        queryset = self.perform_update_or_create(request.data)
        serialized_queryset = self.get_serializer(queryset, many=True)
        return Response(serialized_queryset.data, status=status.HTTP_200_OK)
    
    def perform_update_or_create(self, validated_data):
        course = get_object_or_404(Course, id=self.kwargs.get('course_id'))
        serializer = self.get_serializer()
        queryset = serializer.update_or_create(validated_data, course)
        return queryset