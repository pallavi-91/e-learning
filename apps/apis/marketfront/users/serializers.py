from asyncio import exceptions
from multiprocessing import context
from django.conf import settings
from django.conf.global_settings import LANGUAGES

from django.contrib.auth import authenticate, get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.db.models.query import QuerySet

from rest_framework import serializers, exceptions
from rest_framework.serializers import Serializer, ModelSerializer
from apps.courses.models.lectures import ImageUpload
from apps.status import CourseStatus, RefundStatus
from apps.transactions.models import Transactions
from apps.utils.query import get_object_or_none
import uuid
from apps.courses.models import Course
from apps.users.models import (
    ForgotPasswordToken,
    Instructor,
    CartItem,
    Cart,
    UserClass,
    Order,
    OrderToken,
    SubscribedNewsLater
)
from apps.transactions.models import RefundRequest



class SignupSerializer(ModelSerializer):
    """ signup serializer
    """
    password = serializers.CharField(write_only=True)

    # this field is that if user login and has as a guest carts item this will automatically add to the cart of the user 
    courses = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Course.objects.filter(is_deleted=False,status=CourseStatus.STATUS_PUBLISHED)),
        required=False)

    order_token = serializers.UUIDField(required=False,allow_null=True)
    class Meta:
        model = get_user_model()
        fields = (
            'first_name',
            'last_name',
            'email',
            'password',
            'courses',
            'order_token'
        )

    @transaction.atomic
    def create(self, data):
        courses = data.pop('courses',[])
        order_token = data.pop('order_token',None)

        instance = super(SignupSerializer, self).create(data)
        instance.set_password(data.get('password'))
        instance.is_active = True
        instance.save()

        if order_token:
            obj = get_object_or_none(OrderToken,token=order_token,is_used=False)
            if obj:
                obj.link_order(instance)

        for course in courses:
            instance.cart.add_to_cart(course)

        return instance


class ChangePasswordSerializer(ModelSerializer):
    """ forgot password serializer
    """
    current_password = serializers.CharField(allow_null=True)
    confirm_password = serializers.CharField(min_length=settings.PASSWORD_MIN_LENGTH)
    code = serializers.CharField()

    def __init__(self, *args, **kwargs):
        # setting this to `True` will force
        # to check for the current_password field and
        # force to validate it.
        self.request = kwargs.pop('request', None)
        self.require_current_password = kwargs.pop('check_current', False)

        return super().__init__(*args, **kwargs)

    class Meta:
        model = get_user_model()
        optional_fields = ['current_password']
        fields = (
            'id',
            'current_password',
            'password',
            'confirm_password',
            'code'
        )

    def validate_password(self, password):
        """ check if the passwords are the same
        """
        confirm = self.initial_data.get('confirm_password')
        if password != confirm:
            raise serializers.ValidationError(_("Password did not match"))

        return password

    def validate_code(self, code):
        """ check if the code is valid.
            criteria: was not activated, exists
        """
        token = get_user_model()().get_passwordtoken(code)

        if self.instance != token.user or token.is_activated:
            raise serializers.ValidationError(_("This token is not valid"))

        return code

    def validate_current_password(self, password):
        if not self.require_current_password: return password

        user = authenticate(request=self.request,
            email=self.instance.email, password=password)
        if not user:
            raise serializers.ValidationError('Password is incorrect')
        
        return password

    def update(self, instance, data):
        """ update
        """
        # update the password
        instance.set_password(data.get('password'))
        instance.save()
        # update the password token
        token = instance.get_passwordtoken(data.get('code'))
        token.is_activated = True
        token.save()

        return instance


class InstructorSerializer(ModelSerializer):

    class Meta:
        model = Instructor
        fields = (
            'id',
            'user',
            'instructor_consent',
            'date_created',
            'date_updated',
        )
        read_only_fields =['user']


class UserSerializer(ModelSerializer):
    instructor = InstructorSerializer(read_only=True)
    languages = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'handle',
            'instructor',
            'first_name',
            'last_name',
            'email',
            'headline',
            'bio',
            'photo',
            'language',
            'languages',
            'stats',
            'balance',
            'paypal_email',
            'profile_completion',
        )

    def get_languages(self, instance):
        """ return the list of available
            languages
        """
        return dict(LANGUAGES)

    def get_stats(self, instance):
        """ return user statistics
        """
        return instance.stats


class PersonalInfoSerializer(ModelSerializer):
    email = serializers.CharField(required=False)
    bio = serializers.CharField(min_length=60,required=False)

    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'photo',
            'headline',
            'language',
            'bio',
            'email',
            'paypal_email',
        )

    def validate_email(self, email): 
        request= self.context.get("request")
        user = get_object_or_none(get_user_model(),email=email); 
        if not user: return email

        if user.id == request.user.id:
            raise serializers.ValidationError(_('This is your current email')) 

        raise serializers.ValidationError(_('Email already taken')) 
    

class CartSerializer(ModelSerializer):

    class Meta:
        model = CartItem
        read_only_fields = ('cart',)
        fields = (
            'id',
            'course',
            'date_added',
        )

    def to_representation(self, instance):
        from apps.apis.marketfront.courses.serializers import CourseSerializer

        r =  super().to_representation(instance)
        r['course'] = CourseSerializer(instance.course,context=self.context).data

        return r

    def validate_course(self,data):
        user = self.context.get('request').user
        if data.user.id == user.id:
            raise serializers.ValidationError(_('You owned this course'))
        
        if user.user_classes.filter(course=data,is_purchased=True).exists():
            raise serializers.ValidationError(_('You already bought this course'))
        if data.pricing.tier_level <= 0:
            raise serializers.ValidationError(_('This course is free'))

        return data



class UserShortSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'headline',
            'bio',
            'language',
            'email',
            'photo',
        )

class InstructorUserSerializer(ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = (
            'id',
            'first_name',
            'last_name',
            'headline',
            'bio',
            'language',
            'email',
            'photo',
        )

    def to_representation(self, instance):
        d = super().to_representation(instance)
        d['stats'] = instance.stats
        return d

class CheckoutSerializer(Serializer):
    """ checkout serializer
    """
    courses = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=Course.objects.all()),
        required=False
    )
    # email = serializers.EmailField(required=True)    
    # full_name = serializers.CharField(max_length=120,required=True)    


    def validate_email(self, email):
        auth_user = self.context.get('request').user

        if auth_user.is_authenticated: return email
        """ check if email belongs to a
            registered and active user.
        """
        user = get_object_or_none(get_user_model(),email=email)
        if user:
            raise serializers.ValidationError(
                "Email already registered",
                code="invalid")

        return email

    @transaction.atomic
    def generate_url(self):
        # get request
        user = self.context.get('request').user
        # email = self.validated_data.get('email')
        # full_name = self.validated_data.get('full_name')
        cart = user.cart if user.is_authenticated else \
               self.__create_cart(self.validated_data.get('courses',[]))
        order = cart.checkout()

        return order.paypal_createorder()


    @transaction.atomic
    def __create_cart(self, items):
        """ create a cart instance
            for anonymous users
        """

        email = self.validated_data.get('email')
        full_name = self.validated_data.get('full_name')
        def __course(i): return {'course': i.id}
        # Create user instance for anonymous user based on email 
        # TODO: send the email and password of the anonymous
        # user = User.objects.create(email=email,first_name=full_name,is_active=True)
        # cart = user.cart
        cart = Cart.objects.create()
        for course in items:
            CartItem.objects.create(course=course,cart=cart)

        return cart


class OrderSerializer(ModelSerializer):

    total = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id',
            'user',
            'status',
            'refund',
            'refund_status',
            'date_refunded',
            'date_updated',
            'transactions',
            'classes',
            'total',
        )

    def get_total(self, instance):
        return sum(instance.classes.values_list('price', flat=True))

    def to_representation(self, instance):
        from apps.apis.marketfront.courses.serializers import ClassSerializer

        resp = super().to_representation(instance)
        resp['classes'] = ClassSerializer(
            instance.classes.all(), many=True).data

        return resp


class ForgotPasswordSerializer(Serializer):
    """ password reset token
    """
    email = serializers.EmailField()

    user = None

    def validate_email(self, email):
        """ check if email belongs to a
            registered and active user.
        """
        users = get_user_model().objects \
            .filter(email=email, is_active=True)
        if not users.exists():
            raise serializers.ValidationError(
                "Email is not registered",
                code="invalid")

        self.user, = users

        return email

    def create(self):
        """ create password token
        """
        instance,is_created = ForgotPasswordToken.objects.get_or_create(user=self.user)
        if not is_created:
            instance.code = uuid.uuid4()
        instance.send()

        return instance


class ResetPasswordSerializer(Serializer):
    code = serializers.UUIDField(required=True,write_only=True)
    new_password = serializers.CharField(required=True,write_only=True,min_length=settings.PASSWORD_MIN_LENGTH)

    def validate_code(self,data):
        token = get_object_or_none(ForgotPasswordToken,code=data)
        if not token:
            raise serializers.ValidationError(_("Invalid or expired code"),code="invalid")
            
        self.token = token

        return data

    def update_password(self):
        password = self.validated_data.get('new_password')

        self.token.user.set_password(password)
        with transaction.atomic():
            self.token.user.save()
            self.token.delete()

        return self.token.user



class PaymentSerializer(Serializer):
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    email = serializers.EmailField(required=True)    

    def validate_email(self, email):
        auth_user = self.context.get('request').user

        if auth_user.is_authenticated: return email
        """ check if email belongs to a
            registered and active user.
        """
        user = get_object_or_none(get_user_model(),email=email)
        if user:
            raise serializers.ValidationError(
                "Email already registered",
                code="invalid")

        return email

    @transaction.atomic
    def generate_url(self):
        auth_user = self.context.get('request').user

        email = self.validated_data.get('email')
        order = self.validated_data.get('order')
        if not auth_user.is_authenticated:
            order.user = get_user_model().objects.create(email=email,is_active=True)
            order.save()
            
        return order.paypal_createorder()


class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transactions
        fields = (
            'id',
            'order',
            'type',
            'status',
            'gross_amount',
            'gateway_charge',
            'currency_code',
            'channel_type',
            'payout_status',
            'date_updated',
            'platform_fee',
            'net_amount',
            'can_refund',
        )


class PurchaseHistorySerializer(ModelSerializer):
    course = serializers.SerializerMethodField()

    class Meta:
        model = Transactions
        fields = (
            'id',
            'course',
            'user',
            'type',
            'status',
            'net_amount',
            'payment_type',
            'date_updated',
            'currency_code',
            'can_refund',
            'refund',
            'refund_status',
            'date_refunded',
        )

    def get_course(self, instance):
        from apps.apis.marketfront.courses.serializers import ClassSerializer
        return ClassSerializer(
            UserClass.objects.get(id=instance.class_id)).data


class ReportSerializer(Serializer):

    month = serializers.CharField()
    transactions = TransactionSerializer(many=True)

    class Meta:
        model = Transactions


class TransactionMonthTotalSerializer(Serializer):

    class Meta:
        model = Transactions


    def calculate_totals(self,qs: QuerySet):
        affiliates = qs.filter(channel_type=self.Meta.model.AFFILIATE)
        ad_programs = qs.filter(channel_type=self.Meta.model.AD)
        organics = qs.filter(channel_type=self.Meta.model.ORGANIC)
        affiliates_total = ad_programs_total = organics_total = 0

        for aff in affiliates:
            affiliates_total += aff.net_amount

        for aff in ad_programs:
            ad_programs_total += aff.net_amount

        for aff in organics:
            organics_total += aff.net_amount


        return {
            'affiliates_total': round(affiliates_total,2), 
            'ad_programs_total': round(ad_programs_total,2), 
            'organics_total': round(organics_total,2), 
            'totals': round(affiliates_total + organics_total + ad_programs_total,2) 
        }


class ImageUploadSerializer(ModelSerializer):

    class Meta:
        model = ImageUpload
        read_only_fields = ['user']
        fields = '__all__'

    def create(self, validated_data):
        request = self.context.get('request')
        section = validated_data.get('section')
        # if the section is not on the current user raise an error
        if section.course.user.id != request.user.id:
            raise exceptions.PermissionDenied()

        return super(ImageUploadSerializer,self).create(validated_data)



class RefundRequestSerializer(ModelSerializer):

    class Meta:
        model = RefundRequest
        read_only_fields = ['user','transaction','status']
        fields = '__all__'


    @transaction.atomic
    def create(self,validated_data):
        transaction = validated_data.get('transaction')
    
        if not transaction or not transaction.can_refund:
            raise exceptions.PermissionDenied(_('This order is not refundable'))

        transaction.refund_status = RefundStatus.REFUND_PENDING
        transaction.save()
        return super(RefundRequestSerializer,self).create(validated_data)

class PayoutBalanceSerializer(serializers.Serializer):
    balance = serializers.FloatField(default=0)


class SubscribedNewsLaterSerializer(serializers.ModelSerializer):

    class Meta:
        model = SubscribedNewsLater
        fields = ['email_address']