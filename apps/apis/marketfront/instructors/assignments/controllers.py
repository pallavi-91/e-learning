from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from django_filters import rest_framework as filters
from apps.utils.filters import IOrderingFilter
from django.db.models import Avg, Case, Count, F, Sum, When, FloatField, Value, Q, Max
from django.db.models.functions import Coalesce, Round
from .serializers import AssignmentSerializer
from rest_framework import viewsets
from apps.status import CourseStatus
from apps.courses.models import Assignment
from rest_framework.response import Response
from rest_framework import status

class AssignmentView(viewsets.ModelViewSet):
    serializer_class = AssignmentSerializer
    filter_backends = [OrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_fields = ['category', 'subcategory','status']
    ordering_fields = ['title']
    queryset = Assignment.objects.all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset().filter(user = request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
