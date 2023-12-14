from rest_framework import serializers
from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer, UserClassSerializer
from apps.status import RefundStatus, ShareTypes
from apps.users.models import Order
from apps.transactions.models import Transactions, TransactionTypes
from django.db.models import Avg, Q, Count, When, Case, F, Sum, Value, FloatField
from django.db.models.functions import Coalesce, TruncDate, Round
from apps.apis.admin.sales.query import instructor_share, platform_share

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'date_created', 'user', 'status')

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['transactions'] = instance.order_transactions.count()
        context['sale_price'] = sum(instance.order_transactions.filter(
            refund=False).values_list('gross_amount', flat=True))
        context['sellers'] = instance.classes.select_related('course', 'course__user').values_list('course__user__id', flat=True).distinct()
        return context

class OrderTransactionSerializer(serializers.ModelSerializer):
    channel_name = serializers.SerializerMethodField()
    platform_earning = serializers.SerializerMethodField()
    instructor_earning = serializers.SerializerMethodField() 
    affiliate_earning = serializers.SerializerMethodField()
    platform_earning = serializers.SerializerMethodField()

    class Meta:
        model = Transactions
        fields = ['id', 'transaction_id', 'gross_amount', 'channel_name', 'student', 'instructor',
                  'platform_earning', 'instructor_earning', 'type', 'affiliate_earning', 'platform_earning',
                  'status', 'date_created', 'refund', 'refund_status']
     
    
    def get_channel_name(self, obj):
        return ShareTypes[obj.channel_obj.share_types].title()
    
    def get_platform_earning(self, obj):
        return obj.platform_fee

    def get_instructor_earning(sel, obj):
        return obj.instructor_fee

    def get_affiliate_earning(sel, obj):
        return obj.affiliate_fee

    def get_platform_earning(sel, obj):
        return obj.platform_fee
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['user_class'] = UserClassSerializer(instance.user_class).data
        transactions = instance.order.order_transactions.exclude(type=TransactionTypes.PAYOUT).filter(refund=True)
        if transactions.exists():
            context['refund_transaction'] = transactions.last().id
        
        context['refund_requests'] = instance.refund_requests.filter(status=RefundStatus.REFUND_PENDING).count()
        return context

    
class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'date_created', 'user', 'status')

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['order_detail'] = instance.order_transactions.prefetch_related('user_class').exclude(type=TransactionTypes.PAYOUT)\
            .aggregate(
                no_of_products = Count('user_class', distinct=True),
                purchase_price=Coalesce(Round(Sum(Case(
                    When(type=TransactionTypes.SALE, then=F('gross_amount')),
                    default=0,
                    output_field=FloatField()
                ))),  Value(0), output_field=FloatField()),
                instructor_earnings=Coalesce(Round(Sum(Case(
                            When(Q(type=TransactionTypes.SALE) & Q(refund=False), 
                                then=(
                                        F('gross_amount') - (
                                            F('gateway_charge') + F('vat_amount') 
                                        ) 
                                    )* (instructor_share/100)
                                ),
                            default=0,
                            output_field=FloatField()
                        ))), Value(0), output_field=FloatField()),
                
                platform_earnings=Coalesce(Round(Sum(Case(
                            When(Q(type=TransactionTypes.SALE) & Q(refund=False), 
                                then=(
                                        F('gross_amount') - (
                                            F('gateway_charge') + F('vat_amount') 
                                        ) 
                                    )* (platform_share/100)
                                ),
                            default=0,
                            output_field=FloatField()
                        ))), Value(0), output_field=FloatField()),
            )
        transactions = instance.order_transactions.exclude(type=TransactionTypes.PAYOUT).filter(refund=False)
        if transactions.exists():
            transaction = transactions.first()
            context['payment_type'] = PaymentTypeSerializer(transaction.payment_type).data
            context['payment_type'] .update({
                'gateway_charge': transaction.gateway_charge
            })
        
        return context
