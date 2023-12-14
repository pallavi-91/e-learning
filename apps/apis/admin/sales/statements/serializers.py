import pdb
from rest_framework import serializers,exceptions
from apps.apis.admin.pricing.serializers import CurrencySerializer
from apps.apis.admin.sales.transactions.serializers import PaymentTypeSerializer
from apps.currency.models import Currency
from apps.statements.models import Statement, StatementTransactions
from apps.users.models import Order
from apps.transactions.models import PaymentType, TransactionTypes, Transactions
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When, FloatField, Value
from django.db.models.functions import Coalesce, Round
from apps.apis.admin.sales.query import channel_key_value
    
class StatementSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    class Meta:
        model = Statement
        fields = ['id','period','total_earnings','status','date_created',]
        
    def get_total_earnings(self,obj):
        earnings = 0
        statement_trans = StatementTransactions.objects.filter(statement=obj.id)
        for trans in statement_trans:
            earnings += trans.platform_fee
        return round(earnings, 2)

class StatementTransactionSerializer(serializers.ModelSerializer):
    platform_earnings = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()
    instructor_earnings = serializers.SerializerMethodField()
    
    class Meta:
        model = StatementTransactions
        fields = ['platform_earnings', 'instructor_earnings', 'net_amount']

    def get_platform_earnings(self, obj):
        return obj.platform_fee
    
    def get_instructor_earnings(self, obj):
        return obj.instructor_fee
    
    def get_net_amount(self, obj):
        return obj.net_amount
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        context.update(instance.transaction_detail)
        context['event'] = instance.event
        context['st_id'] = instance.id
        return context
        
class StatementDetailSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Statement
        fields = ['id','period','status','date_created',]
    
    def to_representation(self, instance):
        context = super().to_representation(instance)
        results = {
            "total_earnings": 0,
            "total_orders": set(),
            "total_refund": 0,
            "total_transactions": set(),
            "thkee_earnings": 0,
            "instructor_earnings": 0,
        }
        transactions = instance.statements.all()
        for strans in transactions:
            if not strans.transaction.refund:
                results['total_earnings'] += strans.net_amount
                results['thkee_earnings'] += strans.platform_fee
                results['instructor_earnings'] += strans.instructor_fee
            results['total_transactions'].add(strans.transaction.id)
            if strans.transaction.refund:
                results['total_refund']+= strans.transaction.gross_amount
            
            results['total_orders'].add(strans.transaction.order)
            
        results['total_transactions'] = len(results['total_transactions'])
        results['total_orders'] = len(results['total_orders'])
        results['thkee_earnings'] = round(results['thkee_earnings'], 2)
        results['instructor_earnings'] = round(results['instructor_earnings'], 2)
        context.update(results)
        return context
   

class StatementTransactionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatementTransactions
        fields = ['id',]
    
    # def get_discount(self, obj):
    #     discount_amount = obj.transaction_coupons.aggregate(discount_amount=Coalesce(Sum('discount_value'), 0, output_field=FloatField()))
    #     return discount_amount.get('discount_amount')
    
    # def get_discount_coupon(self, obj):
    #     coupon_codes = ",".join(obj.transaction_coupons.values_list('coupon_code', flat=True))
    #     return coupon_codes    
 

    def to_representation(self, instance):
        context = super().to_representation(instance)
        context.update(instance.transaction_detail)
        context['net_amount'] = instance.net_amount
        context['listed_price'] = instance.listed_price
        context['discount'] = 0
        context['discount_coupon'] = ''
        
        return context
        
