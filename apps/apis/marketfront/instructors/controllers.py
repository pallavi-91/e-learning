import json
import calendar
from itertools import groupby

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, GenericViewSet
from apps.status import TransactionTypes
from apps.users.paginations import  ReportPagination, TransactionPagination
from apps.utils.paginations import ViewSetPagination

from apps.utils.query import SerializerProperty, InjectUserToData, get_object_or_none
from apps.users.models import UserClass
import datetime
from dateutil import relativedelta

from .serializers import (
    ReportSerializer,
    TransactionMonthTotalSerializer,
    TransactionSerializer,
    UserSerializer,
    InstructorSerializer,
)


class UserView(SerializerProperty, GenericViewSet):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get(self,request,**kwargs):
         instructor = get_object_or_404(InstructorSerializer.Meta.model,**kwargs)
         return Response(self.get_serializer(instructor.user).data)


class InstructorView(InjectUserToData, SerializerProperty, ViewSet):
    """ instructors endpoint
    """
    serializer_class = InstructorSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)

 
class ReportsView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ user report
    """
    serializer_class = ReportSerializer
    pagination_class = ReportPagination

    def reports_by_month(self,request,**kwargs):
        month = kwargs.get('month',None) 
        qs = request.user.instructor_transactions.filter(type=TransactionTypes.SALE)
        return qs

    def reports(self, request):
        qs = self.__filter(request.user.instructor_transactions.filter(type=TransactionTypes.SALE))

        serializer = self.serializer_class(
            self.paginate_queryset(qs), many=True)

        return self.get_paginated_response(serializer.data)
    
    def __filter(self, qs):
        def __qs():
            for date, group in groupby(qs, key=lambda i: f"{i.date_updated.month} {i.date_updated.year}"):
                m, y = date.split(" ")
                yield {
                    'month': f"{calendar.month_name[int(m)]} {y}",
                    'transactions': [i for i in group]
                }
        return list(__qs())

    def summary(self, request):
        """ report summary
        """
        current_month = timezone.now().month 
        trans = request.user.instructor_transactions \
                    .filter(type=TransactionTypes.SALE)
        current_month_trans = trans.filter(date_updated__month=current_month)
        purchased = UserClass.objects.filter(is_purchased=True,course__user=request.user)
        def __get_revenues(current=False):
            trans_ = current_month_trans if current else trans
            for t in trans_: yield t.net_amount

        return Response({
            'total_revenues': sum(list(__get_revenues())),
            'current_month_revenue': sum(list(__get_revenues(True))),
            'total_enrollments': purchased.count(),
            'current_month_enrollments': purchased.filter(date_created__month=current_month).count() ,
            'overall_ratings': request.user.instructor.ratings
        })

    def enrollments(self, request):
        """ enrollments
        """
        trans = request.user.instructor_transactions \
                    .filter(type=TransactionTypes.SALE)
        
        def __filter():
            for dt, group in groupby(trans, key=lambda i: f"{i.date_updated.month} {i.date_updated.year}"):
                m, y = dt.split(" ")
                yield {
                    'month': f"{calendar.month_name[int(m)]} {y}",
                    'total': len([i for i in group])
                }

        return Response([i for i in __filter()], status=200)
 

class TransactionView(SerializerProperty, ViewSetPagination, GenericViewSet):
    """ user report
    """
    serializer_class = TransactionSerializer
    pagination_class = TransactionPagination
    filter_backends = [filters.DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['date_updated','date_created']

    def get_queryset(self):
        return self.request.user.instructor_transactions.all()
    
    def list(self,request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.get_serializer(self.paginate_queryset(qs),many=True) 
        return self.get_paginated_response(page.data)


    def reports_by_month(self,request,**kwargs):
        month = kwargs.get('month') 
        current = datetime.datetime.strptime(month,'%Y-%m-%d')
        currentEnd = current + relativedelta.relativedelta(months=1)

        qs = self.filter_queryset(request.user.instructor_transactions.filter(
                type=TransactionTypes.SALE,
                date_created__lt=currentEnd,
                date_created__gt=current
        ))
        page = self.get_serializer(self.paginate_queryset(qs),many=True) 
        return self.get_paginated_response(page.data)


    def totals_by_month(self,request,**kwargs):
        month = kwargs.get('month') 
        current = datetime.datetime.strptime(month,'%Y-%m-%d')
        currentEnd = current + relativedelta.relativedelta(months=1)

        qs = self.filter_queryset(request.user.instructor_transactions.filter(
                type=TransactionTypes.SALE,
                date_created__lt=currentEnd,
                date_created__gt=current
        ))
        data = TransactionMonthTotalSerializer().calculate_totals(qs)
        return Response(data)
