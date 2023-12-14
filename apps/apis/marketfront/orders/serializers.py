from django.conf.global_settings import LANGUAGES

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.serializers import Serializer, ModelSerializer
from apps.apis.marketfront.classes.serializers import ShortClassSerializer
from apps.shares.models import SharePrices
from apps.status import CourseStatus, InstructorGroups, OrderStatus, ShareTypes, TransactionTypes
from apps.transactions.models import PaymentType, Transactions
from apps.utils.query import get_object_or_none
from apps.courses.models import Course
from apps.users.models import (
    CartItem,
    Cart,
    UserClass,
    Order
)

class CheckoutSerializer(Serializer):
    """ checkout serializer
    """
    courses = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Course.objects.filter(status=CourseStatus.STATUS_PUBLISHED)),
        required=False)
    email = serializers.EmailField(required=False)    
    full_name = serializers.CharField(max_length=120, required=False)    
    channel_code = serializers.CharField(max_length=150, required=False)  

    def validate_email(self, email):
        """ check if email belongs to a
            registered and active user.
        """
        request = self.context.get('request')
        if request.user.is_authenticated: 
            return email
        
        user = get_object_or_none(get_user_model(), email=email)
        if user:
            raise serializers.ValidationError("User with this email already exists", code="invalid")

        return email
    
    def validate_courses(self, courses):
        """ check if courses are in cart.
        """
        if not len(courses):
            raise serializers.ValidationError("No course selected", code="invalid")
        return courses

    @transaction.atomic
    def generate_url(self):
        # get request
        user = self.context.get('request').user
        email = self.validated_data.get('email')
        full_name = self.validated_data.get('full_name')
        courses = self.validated_data.get('courses')
        channel_code = self.validated_data.get('channel_code')
        cart = user.cart if user.is_authenticated else \
               self.__create_cart(courses)
        # Get default channel if channel_code is blank
        if channel_code:
            channel = SharePrices.objects.get(code=channel_code)
        else:
            # Use default channel
            channel = SharePrices.objects.get(share_types=ShareTypes.ORGANICS, group_name=InstructorGroups.DEFAULT)
            
        order = cart.checkout(email=email, 
                              full_name=full_name, 
                              channel=channel.to_json(),
                              status=OrderStatus.SAVED)

        return order.paypal_createorder()


    @transaction.atomic
    def __create_cart(self, items):
        """ create a cart instance for anonymous users
        """
        email = self.validated_data.get('email')
        full_name = self.validated_data.get('full_name')
        # TODO: send the email and password of the anonymous
        user = get_user_model().objects.create(email=email, first_name=full_name, is_active=True)
        cart = Cart.objects.create(user=user)
        for course in items:
            CartItem.objects.create(course=course, cart=cart)
        return cart


class OrderSerializer(ModelSerializer):

    class Meta:
        model = Order
        fields = (
            'id',
            'code',
            'user',
            'status',
            'refund',
            'refund_status',
            'date_refunded',
            'date_updated',
        )

    def to_representation(self, instance):

        context = super().to_representation(instance)
        context['classes'] = ShortClassSerializer(instance.classes.all(), many=True, context=self.context).data
        context['total_amount'] = instance.total_amount
        return context


class PaymentSerializer(Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    email = serializers.EmailField(required=True)    

    def validate_email(self, email):
        """ check if email belongs to a
            registered and active user.
        """
        request = self.context.get('request')
        if request.user.is_authenticated: 
            return email
        
        user = get_object_or_none(get_user_model(), email=email)
        if user:
            raise serializers.ValidationError("User with this email already exists", code="invalid")

        return email

    @transaction.atomic
    def generate_url(self):
        auth_user = self.context.get('request').user

        email = self.validated_data.get('email')
        order = self.validated_data.get('order')
        if not auth_user.is_authenticated:
            order.user = get_user_model().objects.create(email=email, is_active=True)
            order.save()
            
        return order.paypal_createorder()


class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = ['payment_gateway', 'payment_method']


class PurchaseHistorySerializer(ModelSerializer):
    class Meta:
        model = Order
        fields = (
            'id',
            'code',
            'user',
            'email',
            'full_name',
            'status',
            'refund',
            'refund_status',
            'date_refunded',
            'date_updated',
        )

    def to_representation(self, instance):

        context = super().to_representation(instance)
        context['classes'] = ShortClassSerializer(instance.classes.all(), many=True, context=self.context).data
        context['total_amount'] = instance.total_amount
        context['payment'] = PaymentTypeSerializer(instance.payment_type, context=self.context).data
        return context


class PayoutBalanceSerializer(serializers.Serializer):
    balance = serializers.FloatField(default=0)