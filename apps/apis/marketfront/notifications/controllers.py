import pdb
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _
from rest_framework.response import Response
from .serializers import NotificationSerializer
from apps.utils.query import SerializerProperty, get_object_or_none
from apps.utils.paginations import ViewSetPagination
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework.filters import OrderingFilter,SearchFilter
from rest_framework.viewsets import ViewSet, GenericViewSet, ModelViewSet
from rest_framework.exceptions import APIException, NotFound, ValidationError

class NotificationView(SerializerProperty,ViewSetPagination, GenericViewSet):
    serializer_class = NotificationSerializer
    def get_queryset(self,request, **kwargs):
        qs = self._model.objects.filter(
            user__id = kwargs.get('user_id')
        )
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page,many=True)
        return self.get_paginated_response(serializer.data)