from django.shortcuts import get_object_or_404
from apps.courses.models import Course 
from rest_framework import viewsets
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter,SearchFilter
from apps.utils.filters import IOrderingFilter
from .serializers import CourseQnASerializer
from apps.apis.admin.paginations import CommonPagination
from django_filters import rest_framework as filters


class CourseQnaView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CourseQnASerializer
    pagination_class = CommonPagination
    queryset = CourseQnASerializer.Meta.model.objects.select_related('user').all()
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    search_fields = ['id', 'rate', 'content',]

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user_class__course__code=self.kwargs.get('code'))

   
    