from rest_framework import serializers
from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer, TransactionSerializer, UserClassSerializer
from apps.transactions.models import RefundRequest, Transactions, TransactionTypes
from django.db.models import Avg, Q, Count, When, Case, F, Sum, IntegerField, FloatField
   
class RefundRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['id', 'user', 'refund_type', 'transaction', 'reason', 'status','date_created', 'date_updated']
        read_only_fields = ['date_created', 'date_updated', 'refund_amount']
        
        
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['product'] = UserClassSerializer(instance.transaction.user_class).data
        order_transactions = instance.transaction.order.order_transactions.exclude(type=TransactionTypes.PAYOUT)
        result = order_transactions.aggregate(total_transactions=Count('id', filter=Q(type=TransactionTypes.SALE)), 
                                              refund_transactions=Count('id', filter=Q(type = TransactionTypes.REFUND)))
        context.update(result)
        return context

class RefundRequestDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundRequest
        fields = ['id', 'user','refund_type', 'reason', 'status','date_created', ]
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context['product'] = UserClassSerializer(instance.transaction.user_class).data
        context['transaction'] = TransactionSerializer(instance.transaction).data
        context['payment_type'] = PaymentTypeSerializer(instance.transaction.payment_type).data
        context['payment_type'] .update({
                'gateway_charge': instance.transaction.gateway_charge
            })
        
        context['course_progress'] = instance.transaction.user_class.actual_progress
        context['progress_total'] = instance.transaction.user_class.subsections_total
        context['refundable'] = instance.transaction.can_refund
        context['is_eligible'] = instance.transaction.is_eligible
        context['remaining_days'] = instance.transaction.user_class.remaining_days
        return context