from apps.apis.admin.paginations import CommonPagination
from .serializers import CountrySerializer
from rest_framework import viewsets
from apps.countries.models import Country
from apps.courses.models import CoursePrice
from rest_framework.response import Response
from rest_framework import pagination
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.permissions import IsAdminUser


class CountryView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = CountrySerializer
    queryset = Country.objects.all()
    # pagination_class = CommonPagination
    filter_backends = [OrderingFilter,SearchFilter,filters.DjangoFilterBackend]
    filterset_fields = ['allow_billing', 'subject_to_vat']
    ordering_fields = ['name','date_updated']
    search_fields = ['id','name', 'two_letter_iso_code','three_letter_iso_code','numeric_iso_code', 'sort_number']
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)