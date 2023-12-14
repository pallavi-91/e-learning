from django.shortcuts import get_object_or_404
from apps.apis.admin.courses.reviews.filters import CourseReviewFilter
from apps.courses.models import Course 
from rest_framework import viewsets
from rest_framework import generics, status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter,SearchFilter
from apps.utils.filters import IOrderingFilter
from .serializers import CourseReviewSerializer
from apps.apis.admin.paginations import CommonPagination
from django_filters import rest_framework as filters


class CourseReviewView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CourseReviewSerializer
    pagination_class = CommonPagination
    queryset = CourseReviewSerializer.Meta.model.objects.all()
    filter_backends = [IOrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_class  = CourseReviewFilter
    search_fields = ['id', 'rate', 'content',]

    def get_queryset(self):
        return super().get_queryset().filter(course__code=self.kwargs.get('code'))

   
    