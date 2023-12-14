import pdb
from rest_framework.permissions import IsAdminUser
from rest_framework import  viewsets
from apps.apis.admin.sales.statements.filters import StatementSearchFilter
from apps.statements.models import Statement, StatementTransactions
from apps.utils.query import get_object_or_none
from .serializers import StatementDetailSerializer, StatementSerializer, StatementTransactionSerializer, StatementTransactionInvoiceSerializer
from apps.transactions.models import TransactionTypes, Transactions
from apps.users.models import Order
from rest_framework.response import Response
import arrow
from django.db.models import Q, Count, When, Case, F, Sum, IntegerField, FloatField
from django.db.models.functions import Coalesce
from django.db.models.functions import TruncMonth, TruncDate
from apps.apis.admin.sales.query import instructor_share, platform_share

class StatementView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = StatementSerializer
    filterset_class = StatementSearchFilter
    search_fields = ['id', 'period',]
    queryset = Statement.objects.all()
        
    def get_total_orders(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        last_start, last_end = arrow.now().shift(months=-1).span('month')
        context = dict()
        
        # Get total orders
        context['total_orders'] = Order.objects.count()
        context['current_month_orders'] = Order.objects.filter(Q(date_created__date__gte=current_start.date()) & Q(date_created__date__lte=current_end.date())).count()
        context['last_month_orders'] = Order.objects.filter(Q(date_created__date__gte=last_start.date()) & Q(date_created__date__lte=last_end.date())).count()
        increased_order = context['current_month_orders'] - context['last_month_orders']
        context['order_increase_from_last_month'] = round((increased_order/context['current_month_orders']) * 100, 2) if increased_order > 0 else 0
        
        # Get total transactions
        context['total_transactions'] = Transactions.objects.sales_transactions().count()
        context['current_month_transactions'] = Transactions.objects.sales_transactions().filter(Q(date_created__date__gte=current_start.date()) & Q(date_created__date__lte=current_end.date())).count()
        context['last_month_transactions'] = Transactions.objects.sales_transactions().filter(Q(date_created__date__gte=last_start.date()) & Q(date_created__date__lte=last_end.date())).count()
        increased_transactions = context['current_month_transactions'] - context['last_month_transactions']
        context['transactions_increase_from_last_month'] = round((increased_transactions/context['current_month_transactions']) * 100, 2) if increased_order > 0 else 0

        return Response(context)
    
    def transactions(self, request, *args, **kwargs):
        obj = self.get_object()
        statements_transactions = obj.statements.all()
        serializer = StatementTransactionSerializer(statements_transactions, many=True)
        return Response(serializer.data)
    
    def details(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = StatementDetailSerializer(obj)
        return Response(serializer.data)
    
    def chart_data_summery(self, request, *args, **kwargs):
        totals = Transactions.objects.sales_transactions().annotate(date=TruncDate('date_updated'))\
            .values('date')\
            .annotate(
                total_sales=Count(Case(
                    When(type=TransactionTypes.SALE, then='id'),
                    default=0,
                    output_field=IntegerField()
                )),
                total_earnings=Sum(Case(
                    When(Q(type=TransactionTypes.SALE) & Q(refund=False), then=F('gross_amount') * (platform_share/100)),
                    default=0,
                    output_field=FloatField()
                )),
                total_refund=Sum(Case(
                    When(type=TransactionTypes.REFUND, then='gross_amount'),
                    default=0,
                    output_field=IntegerField()
            )))\
            .values( 'date', 'total_sales', 'total_earnings', 'total_refund').order_by('date')
        return Response(totals)
    
    
    def invoice_detail(self, request, *args, **kwargs):
        instance = get_object_or_none(StatementTransactions, **kwargs)
        serializer = StatementTransactionInvoiceSerializer(instance)
        return Response(serializer.data)