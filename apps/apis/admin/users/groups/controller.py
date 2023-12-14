from django.db.models import Avg, Count, Prefetch, Q, Sum
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from apps.apis.admin.paginations import CommonPagination
from .serializers import InstructorGroupSerializer, GroupDetailSerializer
from django_filters import rest_framework as filters
from apps.utils.filters import IOrderingFilter
from rest_framework.filters import SearchFilter
from apps.users.models import User
from django.db.models import Avg, Q, Sum, Case, Count, F,  When
import arrow

class InstructorGroupView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = InstructorGroupSerializer
    pagination_class = CommonPagination
    filter_backends = [IOrderingFilter,
                       SearchFilter, filters.DjangoFilterBackend]
    queryset = InstructorGroupSerializer.Meta.model.objects.all()
    search_fields = ['id', 'group_name']

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def groups_count(self, request, *args, **kwargs):
        context= self.get_queryset().aggregate(active_groups=Count(
                                                            Case(When(is_active=True, then='id'),), distinct=True),
                                                nactive_groups=Count(
                                                            Case(When(is_active=False, then='id'),), distinct=True))
        return Response(context)

    def update_group(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = GroupDetailSerializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
