from dataclasses import fields
import pdb
from rest_framework import serializers
from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer
from apps.apis.admin.users.instructors.serializers import UserProfileSerializer
from apps.status import HoldTransactionStatus, RefundStatus
from apps.transactions.models import HoldTransaction, RefundRequest, Transactions, TransactionTypes
from django.db.models import Avg, Q, Count, When, Case, Value, F, Sum, IntegerField, FloatField
from django.db.models.functions import Coalesce, Round
from apps.transactions.models import InstructorPayouts, PayoutType, PayoutStatus, TransactionPayout
from apps.apis.admin.sales.query import channel_key_value

def get_instructor_share_amount():
    return (
            F('transaction__gross_amount') - (
                F('transaction__gateway_charge') + F('transaction__vat_amount') 
            ) 
        )* (channel_key_value('instructor_share','transaction__channel')/100)

def get_platform_share_amount():
    return (
            F('transaction__gross_amount') - (
                F('transaction__gateway_charge') + F('transaction__vat_amount') 
            ) 
        )* (channel_key_value('platform_share','transaction__channel')/100)
# float(self.gross_amount - (self.gateway_charge + self.vat_amount) )
def get_net_amount():
    return F('transaction__gross_amount') - (
                F('transaction__gateway_charge') + F('transaction__vat_amount') 
            )
    

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorPayouts
        fields = ['id', 'payout_type', 'period', 'status', 'payout_type','date_created', 'date_updated', 'due_date']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['instructor'] = UserProfileSerializer(instance.user).data
        result = instance.transactions.select_related('transaction').aggregate(
                            total_transactions=Count('transaction__id', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            refund_amount=Coalesce(
                                            Sum('transaction__gross_amount', filter=(Q(transaction__refund = True)&Q(transaction__type=TransactionTypes.REFUND )), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE)&Q(transaction__refund = False)), 
                                                            then=get_instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                        )
        context.update(result)
        context['account_active'] = instance.user.is_active
        context['hold_by'] = {}
        context['inactive_reason'] = ""
        
        if not context['account_active'] and hasattr(instance.user, 'user_account'):
            context['hold_by'] = UserProfileSerializer(instance.user.user_account.hold_by).data
            context['inactive_reason'] = instance.user.user_account.inactive_reason
        return context

class PaidPayoutDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorPayouts
        fields = ['id', 'period', 'status', 'payout_type','paid_at', 'date_updated']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['instructor'] = UserProfileSerializer(instance.user).data
        result = instance.transactions.select_related('transaction').aggregate(
                            total_transactions=Count('transaction__id', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            total_orders=Count('transaction__order', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            refund_amount=Coalesce(
                                            Sum('transaction__gross_amount', filter=(Q(transaction__refund = True) & Q(transaction__type=TransactionTypes.REFUND)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            total_refund=Coalesce(
                                            Count('transaction__id', filter=(Q(transaction__refund = True)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            refund_success=Coalesce(
                                            Count('transaction__id', filter=(Q(transaction__refund = True)&Q(transaction__refund_status=RefundStatus.REFUND_SUCCESS )), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE)&Q(transaction__refund = False)), 
                                                            then=get_instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                        )
        context.update(result)
        
        return context

class PaidPayoutDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorPayouts
        fields = ['id', 'period', 'status', 'payout_type','paid_at', 'date_updated']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['instructor'] = UserProfileSerializer(instance.user).data
        result = instance.transactions.select_related('transaction').aggregate(
                            total_transactions=Count('transaction__id', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            total_orders=Count('transaction__order', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            refund_amount=Coalesce(
                                            Sum('transaction__gross_amount', filter=(Q(transaction__refund = True) & Q(transaction__type=TransactionTypes.REFUND)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            total_refund=Coalesce(
                                            Count('transaction__id', filter=(Q(transaction__refund = True)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            refund_success=Coalesce(
                                            Count('transaction__id', filter=(Q(transaction__refund = True)&Q(transaction__refund_status=RefundStatus.REFUND_SUCCESS )), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE)&Q(transaction__refund = False)), 
                                                            then=get_instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                        )
        context.update(result)
        return context
    
    
class InactivePayoutDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = InstructorPayouts
        fields = ['id', 'period', 'status', 'payout_type','paid_at', 'date_updated']
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['instructor'] = UserProfileSerializer(instance.user).data
        result = instance.transactions.select_related('transaction').aggregate(
                            total_transactions=Count('transaction__id', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            total_orders=Count('transaction__order', filter=Q(transaction__type=TransactionTypes.SALE), distinct=True), 
                            refund_amount=Coalesce(
                                            Sum('transaction__gross_amount', filter=(Q(transaction__refund = True) & Q(transaction__type=TransactionTypes.REFUND)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            bank_payment=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__instructor__instructor__payout_method=self.context.get('bank_transfer')) & Q(transaction__type = TransactionTypes.SALE)),
                                                            then=get_instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            paypal_payment=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__instructor__instructor__payout_method__in=self.context.get('paypal_transfer')) & Q(transaction__type = TransactionTypes.SALE)), 
                                                            then=get_instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            bank_transfer=Coalesce(Round(Count(Case(
                                                        When( (Q(transaction__instructor__instructor__payout_method=self.context.get('bank_transfer')) & Q(transaction__type = TransactionTypes.SALE)),
                                                            then='transaction__id'
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            paypal_transfer=Coalesce(Round(Count(Case(
                                                        When( (Q(transaction__instructor__instructor__payout_method__in=self.context.get('paypal_transfer')) & Q(transaction__type = TransactionTypes.SALE)), 
                                                            then='transaction__id'
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            platform_earnings=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE) & Q(transaction__refund = False)), 
                                                            then=get_platform_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            instructor_earnings=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE) & Q(transaction__refund = False)), 
                                                            then=get_instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                            total_earnings=Coalesce(
                                            Sum('transaction__gross_amount', filter=(Q(transaction__type = TransactionTypes.SALE)), distinct=True),
                                            0,
                                            output_field=FloatField()
                                            ),
                            net_amount=Coalesce(Round(Sum(Case(
                                                        When( (Q(transaction__type = TransactionTypes.SALE)&Q(transaction__refund = False)), 
                                                            then=get_net_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                        )
        context.update(result)
        
        return context


class HoldTransactionSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    class Meta:
        model = HoldTransaction
        fields = ['id', 'user', 'status', 'reason']

class SalesTransactionSerializer(serializers.ModelSerializer):
    
    
    class Meta:
        model = Transactions
        fields = ['id', 'transaction_id', 'gross_amount', 'type', 'order', 'payout_status',
                  'status', 'date_created', 'refund', 'refund_status', 'payment_type']

    def to_representation(self, obj):
        context = super().to_representation(obj)
        context['discount_coupon'] = 'No coupon'
        try:
            context['course_name'] = obj.user_class.course.title
        except:
            raise Exception(f'Missing user class course for the  transaction id `{obj.id}`.')
        context['channel_name'] = obj.channel_obj.share_types
        context['platform_earning'] = obj.platform_fee
        context['instructor_earning'] = obj.instructor_fee
        context['affiliate_earning'] = obj.affiliate_fee
        context['thkee_credit_earning'] = obj.thkee_credit_fee
        context['net_amount'] = obj.net_amount
        context['instructor'] = UserProfileSerializer(obj.instructor).data
        context['payment_type'] = PaymentTypeSerializer(obj.payment_type).data
        context['payment_type'] .update({
            'gateway_charge': obj.gateway_charge
        })
        return context
    
    
class PayoutTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionPayout
        fields = ['id','date_created', 'date_updated']
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        hold_transaction = instance.transaction.hold.select_related('user').filter(status=HoldTransactionStatus.HOLD).first()
        if hold_transaction:
            context['hold_by'] = HoldTransactionSerializer(hold_transaction).data
        serializer = SalesTransactionSerializer(instance.transaction).data
        context.update(serializer)
        
        return context


class AddHoldTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoldTransaction
        fields = ['user', 'transaction', 'reason']


class PayoutHoldTransactionSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    transaction = SalesTransactionSerializer(read_only=True)
    class Meta:
        model = HoldTransaction
        fields = ['id', 'status', 'reason', 'user', 'transaction', 'date_updated', 'date_created']
    
    def to_representation(self, instance):
        context =  super().to_representation(instance)
        payout = instance.transaction.transaction_payout.last().payout
        context['payout'] = {
            "id": payout.id,
            "period": payout.period,
        }
        return context