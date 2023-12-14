import pdb
from rest_framework import serializers
from apps.statements.models import Statement, StatementTransactions
from apps.transactions.models import TransactionTypes, Transactions
from apps.users.models import User
from django.db.models import Sum, Count, FloatField
from django.db.models.functions import Coalesce

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'email',
            'photo',
            'balance',
            'paypal_email',
            'is_active',
            'date_joined',
        )


class InstructorSerializer(serializers.ModelSerializer):
    total_transactions = serializers.SerializerMethodField()
    total_earnings = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()
    total_refunds = serializers.SerializerMethodField()
    total_statements = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    date_created = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'total_transactions', 'total_sales','total_earnings', 'profile', 'total_refunds', 'total_statements', 'date_created',]
    
    def get_date_created(self, obj):
        return obj.date_joined
    
    def get_profile(self, obj):
        return UserSerializer(obj).data
    
    def get_total_transactions(self,obj):
        return StatementTransactions.objects.filter(transaction_detail__instructor=obj.id).values('transaction_detail__id').distinct().count()
    
    def get_total_sales(self,obj):
        return StatementTransactions.objects.filter(transaction_detail__instructor=obj.id,
                                                    transaction_detail__type=TransactionTypes.SALE).values('transaction_detail__id').distinct().count()
    
    def get_total_statements(self,obj):
        return StatementTransactions.objects.filter(transaction_detail__instructor=obj.id).values('statement').distinct().count()
    
    def get_total_refunds(self,obj):
        transactions = StatementTransactions.objects.filter(transaction_detail__instructor=obj.id,
                                                    transaction_detail__type=TransactionTypes.REFUND,
                                                    transaction_detail__refund=True)
        refunded = 0
        for trans in transactions:
            refunded += trans.refund_amount
        return round(refunded, 2)
    
    def get_total_earnings(self,obj):
        earnings = 0
        sales_transactions = StatementTransactions.objects.filter(transaction_detail__instructor=obj.id,
                                                    transaction_detail__type=TransactionTypes.SALE,
                                                    transaction_detail__refund=False)
        for trans in sales_transactions:
            earnings += trans.instructor_fee

        return round(earnings, 2)

class InstructorStatementSerializer(serializers.ModelSerializer):
    total_earnings = serializers.SerializerMethodField()
    total_refunds = serializers.SerializerMethodField()
    class Meta:
        model = Statement
        fields = ['id','period','status','total_earnings','total_refunds','date_created',]
        
    def get_total_earnings(self,obj):
        earnings = 0
        instructor = self.context.get('instructor')
        statement_trans = StatementTransactions.objects.filter(statement=obj.id,
                                                               transaction_detail__instructor=instructor.id,
                                                               transaction_detail__type=TransactionTypes.SALE,
                                                               transaction_detail__refund=False)
        for trans in statement_trans:
            earnings += trans.instructor_fee
        
        return round(earnings, 2)
    
    def get_total_refunds(self,obj):
        refunded = 0
        instructor = self.context.get('instructor')
        statement_trans = StatementTransactions.objects.filter(statement=obj.id, transaction_detail__instructor=instructor.id,)
        for trans in statement_trans:
            refunded += trans.refund_amount
        
        return round(refunded, 2)
