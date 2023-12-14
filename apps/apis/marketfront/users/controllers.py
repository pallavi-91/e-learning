import json
import calendar
from itertools import groupby
import pdb
from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from django.db.models import F
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, GenericViewSet, ModelViewSet
from apps.apis.common.storage import fast_s3_upload, s3_create_presigned_post
from apps.status import TransactionTypes
from apps.users.paginations import ImageUploadPagination, RefundRequestPagination, ReportPagination, TransactionPagination
from apps.utils.helpers import convert2webp
from apps.utils.paginations import ViewSetPagination
from apps.users.tasks import create_notification_setting
from apps.utils.query import SerializerProperty, InjectUserToData, get_object_or_none
from apps.users.models import UserClass, SubscribedNewsLater
import datetime
from dateutil import relativedelta

from .serializers import (
    ImageUploadSerializer,
    RefundRequestSerializer,
    ReportSerializer,
    ResetPasswordSerializer,
    SignupSerializer,
    SubscribedNewsLaterSerializer,
    TransactionMonthTotalSerializer,
    TransactionSerializer,
    UserSerializer,
    InstructorSerializer,
    PersonalInfoSerializer,
    ForgotPasswordSerializer,
    ChangePasswordSerializer,
    CartSerializer,
    UserShortSerializer
)


class UserView(SerializerProperty, GenericViewSet):
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def get(self,request,**kwargs):
         instructor = get_object_or_404(InstructorSerializer.Meta.model,**kwargs)
         return Response(self.get_serializer(instructor.user).data)
    
    def post(self, request, **kwargs):
        serializer = SubscribedNewsLaterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        else:
            raise Exception(serializer.errors.get('email_address'))
        return Response(status=200)


class SignupView(APIView):
    """ user signup endpoint
    """
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(serializer.instance).data, status=201)

class ForgotPasswordView(GenericViewSet):
    authentication_classes = []
    permission_classes = []
    serializer_class = ForgotPasswordSerializer

    def verify_email(self,request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.create()
        return Response(status=200)


    def reset_password(self,request):
        serializer = ResetPasswordSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        serializer.update_password()

        return Response(status=200)


class ChangePasswordView(ViewSet):
    """ user forgot password endpoint
    """
    authentication_classes = ()
    permission_classes = (AllowAny,)
    serializer_class = ChangePasswordSerializer

    def _get_user(self, code):
        # RESET PASSWORD: check if there is a
        # `request.user` and code is not available.
        if self.request.user and not code: return self.request.user

        # FORGOT PASSWORD: no `request.user` and code is provided
        if not self.request.user.is_authenticated and code:
            return get_user_model()().get_passwordtoken(code).user

        raise PermissionError(_("Token is not valid."))

    def token_valid(self, request):
        """ check if the token is valid.
            criteria: token exists, token has not yet been activated
        """
        token = get_user_model()() \
            .get_passwordtoken(code=request.data.get('code'))

        if token and not token.is_activated:
            return Response(status=200)
        return Response(status=400)

    def request_reset(self, request):
        send_email = json.loads(request.query_params.get('send', 'true'))

        user = get_object_or_404(get_user_model(), **request.data)
        token = user.send_passwordreset(send_email=send_email)

        if send_email: return Response(status=204)
        return Response({
            'code': token.code
        }, status=200)

    def reset_password(self, request):
        serializer = self.serializer_class(
            data=request.data,
            instance=self._get_user(request.data.get('code')),
            request=request,
            check_current=json.loads(
                request.query_params.get('change', 'false')),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(status=204)


class ProfileView(ViewSet, GenericViewSet):
    """ authenticated user's endpoint
    """
    serializer_class = UserSerializer

    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=200)

    def update(self, request):
        serializer = PersonalInfoSerializer(
            context=self.get_serializer_context(),
            data=request.data, 
            instance=request.user, 
            partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=201)
    


class InstructorsView(InjectUserToData, SerializerProperty, GenericViewSet):
    """ My instructors list endpoint
    """
    serializer_class = UserShortSerializer
    
    def get_queryset(self):
        instructors = self.request.user.user_classes.select_related('course').annotate(users=F('course__user')).values_list('users', flat=True).distinct()
        return self._model.objects.filter(id__in=instructors)
    
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def become_instructor(self, request):
        if request.user.is_instructor:
            instance = request.user.instructor
            serializer = InstructorSerializer(data=request.data, instance = instance)
        else:
            serializer = InstructorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # import pdb; pdb.set_trace()
        instructor = serializer.save(user=request.user)
        create_notification_setting(request.user)
        return Response(serializer.data, status=201)


class CartView(SerializerProperty, GenericViewSet):
    """ user cart
    """
    serializer_class = CartSerializer

    def get(self, request):
        serializer = self.get_serializer(
            request.user.cart.items.all(),
            many=True
        )
        return Response(serializer.data, status=200)

    @transaction.atomic
    def add(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=request.user.cart)

        return Response(serializer.data, status=201)

    def delete(self, request, **kwargs):
        request.user.cart.items.get(**kwargs).delete()
        serializer = self.get_serializer(
            request.user.cart.items.all(),
            many=True
        )
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

class ImageUploadView(SerializerProperty, ViewSetPagination, ModelViewSet):
    """ user report
    """
    serializer_class = ImageUploadSerializer
    pagination_class = ImageUploadPagination

    def get_queryset(self):
        return self.request.user.image_uploads.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RefundRequestView(SerializerProperty, ViewSetPagination, ModelViewSet):
    """ user report
    """
    serializer_class = RefundRequestSerializer
    pagination_class = RefundRequestPagination
    filter_backends = [OrderingFilter]
    ordering_fields = ['date_created']

    def get_queryset(self):
        return self.request.user.instructor_transactions.all()

    def perform_create(self, serializer):
        transaction = get_object_or_404(self.request.user.instructor_transactions.all(),id=self.kwargs.get('transaction_id'))
        serializer.save(user=self.request.user,transaction=transaction )