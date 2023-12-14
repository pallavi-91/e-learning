import pdb
from rest_framework import serializers
from apps.apis.admin.pricing.serializers import CurrencySerializer
from apps.apis.admin.shares.serializers import SharePriceSerializer
from apps.apis.admin.users.instructors.serializers import UserProfileSerializer
from apps.status import RefundStatus, ShareTypes
from apps.users.models import Order, UserClass
from apps.transactions.models import Transactions, RefundRequest, TransactionTypes, PaymentType
from apps.apis.admin.courses.serializers import CourseSerializer
from django.db.models import Sum, FloatField
from django.db.models.functions import Coalesce

        
class UserClassSerializer(serializers.ModelSerializer):
    course = CourseSerializer()
    user = UserProfileSerializer()
    class Meta:
        model = UserClass
        fields = ['id', 'user', 'course', 'price', 'order', 'is_purchased', 'date_created']

class PaymentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentType
        fields = '__all__'
        
class TransactionSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    discount_coupon = serializers.SerializerMethodField()
    channel_name = serializers.SerializerMethodField()
    platform_earning = serializers.SerializerMethodField()
    instructor_earning = serializers.SerializerMethodField() 
    affiliate_earning = serializers.SerializerMethodField()
    thkee_credit_earning = serializers.SerializerMethodField()
    
    class Meta:
        model = Transactions
        fields = ['id', 'transaction_id', 'discount_coupon', 'student', 'instructor', 'course_name', 'gross_amount', 'channel_name',
                  'platform_earning', 'instructor_earning', 'type', 'affiliate_earning', 'thkee_credit_earning',
                  'status', 'payout_status', 'date_created', 'date_updated', 'refund', 'refund_status', 'payment_type']

    def get_discount_coupon(self, obj):
        return "No coupon"
        
    def get_course_name(self, obj):
        if obj.user_class:
            return obj.user_class.course.title
        return ""

    def get_channel_name(self, obj):
        return ShareTypes[obj.channel_obj.share_types].title()
    
    def get_platform_earning(self, obj):
        return obj.platform_fee

    def get_instructor_earning(sel, obj):
        return obj.instructor_fee

    def get_affiliate_earning(sel, obj):
        return obj.affiliate_fee

    def get_thkee_credit_earning(sel, obj):
        return obj.thkee_credit_fee

    def to_representation(self, instance):
        context = super().to_representation(instance)
        refund_transactions = instance.refund_transactions
        if refund_transactions.exists():
            context['refund_transaction'] = refund_transactions.last().id
        context['payment_type'] = PaymentTypeSerializer(instance.payment_type).data
        context['payment_type'] .update({
            'gateway_charge': instance.gateway_charge
        })
        return context


        
class TransactionInvoiceSerializer(serializers.ModelSerializer):
    discount_coupon = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    listed_price = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()
    currency = CurrencySerializer()
    

    class Meta:
        model = Transactions
        fields = ['id', 'transaction_id', 'student', 'instructor', 'discount_coupon', 'discount', 'listed_price', 'gross_amount', 'net_amount', 'channel',
                  'vat_amount', 'currency', 'payment_type', 'type', 'refund', 'refund_status',
                  'status', 'date_created', ]
    
    def get_listed_price(self, obj):
        return obj.user_class.price
    
    def get_net_amount(self, obj):
        return obj.net_amount
    
    def get_discount(self, obj):
        discount_amount = obj.transaction_coupons.aggregate(discount_amount=Coalesce(Sum('discount_value'), 0, output_field=FloatField()))
        return discount_amount.get('discount_amount')
    
    def get_discount_coupon(self, obj):
        coupon_codes = ",".join(obj.transaction_coupons.values_list('coupon_code', flat=True))
        return coupon_codes
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['refund_requests'] = instance.refund_requests.filter(status=RefundStatus.REFUND_PENDING).count()
        context['payment_type'] = PaymentTypeSerializer(instance.payment_type).data
        context['payment_type'] .update({
                'gateway_charge': instance.gateway_charge
            })
        return context

class TransactionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = ['id', 'transaction_id', 'student', 'instructor', 'status', 'refund', 'refund_status', 'type', 'date_created']
                  
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['invoice'] = TransactionInvoiceSerializer(instance).data
        context['product'] = UserClassSerializer(instance.user_class).data
        refund_transactions = instance.refund_transactions
        if refund_transactions.exists():
            context['refund_transaction'] = refund_transactions.last().id
        
        context['refund_requests'] = instance.refund_requests.filter(status=RefundStatus.REFUND_PENDING).count()
        return context

class TransactionEarningSerializer(serializers.ModelSerializer):
    earnings = serializers.SerializerMethodField()
    refund = serializers.SerializerMethodField()
    chargeback = serializers.SerializerMethodField()
    date_created = serializers.DateTimeField(read_only=True, format="%Y-%m-%d")
    
    class Meta:
        model = Transactions
        fields = ['earnings', 'refund', 'chargeback', 'date_created']
    
    def get_earnings(self, obj):
        context = dict()
        context['platform'] = obj.platform_fee
        context['affiliate'] = obj.platform_fee
        context['instructor'] = obj.platform_fee
        return context
    
    def get_refund(self, obj):
        if obj.refund and obj.type == TransactionTypes.REFUND:
            return obj.gross_amount
        return 0
    
    def get_chargeback(self, obj):
        if obj.refund and obj.refund_status == RefundStatus.REFUND_CHARGEBACK:
            return obj.gross_amount
        return 0
