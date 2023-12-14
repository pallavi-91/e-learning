from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect

from django.utils import timezone
from django.utils.translation import gettext as _
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework import exceptions

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet, GenericViewSet, ModelViewSet
from apps.status import CourseStatus, TransactionTypes
from apps.users.paginations import PurchaseHistoryPagination
from apps.utils.paginations import ViewSetPagination

from apps.utils.query import SerializerProperty, InjectUserToData, get_object_or_none
from apps.users.models import UserClass
from apps.courses.models import Course # avoid circular dependency
from apps.apis.marketfront.classes.serializers import ClassSerializer
        
from .serializers import (
    PaymentSerializer,
    CheckoutSerializer,
    OrderSerializer,
    PurchaseHistorySerializer,
    PayoutBalanceSerializer,
)


class OrderView(SerializerProperty, GenericViewSet):
    """ order related actions
    """
    public_actions = ('checkout', 'payment', 'payment_success',)
    serializer_class = CheckoutSerializer

    def get_queryset(self): # not useful function but needed
        return OrderSerializer.Meta.model.objects.all()


    def get_order_details(self,request,**kwargs):
        order = get_object_or_404(request.user.orders,**kwargs)
        serializer = OrderSerializer(order,context=self.get_serializer_context())
        return Response(serializer.data)

    def enroll_for_free(self,request,**kwargs):
        course = get_object_or_404(Course,**kwargs,is_deleted=False,status=CourseStatus.STATUS_PUBLISHED)
        user_class = get_object_or_none(UserClass,course=course,user=request.user)

        if course.user.id == request.user.id:
            raise exceptions.ValidationError(_('You owned this course'))

        if user_class:
            raise exceptions.ValidationError(_('You are already enrolled on this course'))
        
        if not course.pricing.is_free:
            raise exceptions.ValidationError(_('This course is paid.'))
        
        instance = UserClass.objects.create(
            course=course,
            user=request.user,
            price=course.sale_price,
            currency=course.currency,
            is_purchased=True
        )
        serializer = ClassSerializer(instance,context=self.get_serializer_context())
        return Response(serializer.data, status=200)

    def checkout(self, request):
        """ checkout cart items
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({
            'url': serializer.generate_url()
        }, status=201)

    def payment(self, request):
        """ send the user's data to the payment
            gateway.
        """
        serializer = PaymentSerializer(data=request.data,context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        return Response({
            'url': serializer.generate_url()
        }, status=200)

    def payment_capture(self, request):
        """ callback method that captures the event
            after the user approves/made the payment
            from the paypal server.
        """
        from apps.users.models import Order as OrderModel

        ORDER_ID = request.query_params.get('token')
        # query the order instead of using `request.user.orders`
        # to cater unregistered payers.
        order = get_object_or_404(OrderModel, paypal_orderid=ORDER_ID)
        # capture payment
        order.paypal_sendpayment()

        if order.user:
            order.user.cart.clear()
            
        serializer = OrderSerializer(order,context=self.get_serializer_context())
        # 0 and 1 is true or false in ui router 
        # security.util.ts -> LoginRequired -> clear_cart is being processed there
        return Response(serializer.data)


class PurchaseHistory(SerializerProperty, ViewSetPagination,  GenericViewSet):
    """ user purchase history
    """
    serializer_class = PurchaseHistorySerializer
    pagination_class = PurchaseHistoryPagination

    def get_queryset(self):
        return self.request.user.orders.all()
    
    def list(self, request):
        qs = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
