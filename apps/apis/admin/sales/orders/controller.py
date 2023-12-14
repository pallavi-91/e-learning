import pdb
import arrow
from apps.countries.models import Country
from apps.currency.models import Currency
from apps.transactions.models import Transactions, TransactionTypes
from apps.users.models import Order
from django.db.models.functions import Coalesce
from django.db.models import Avg, Count, Prefetch, Q, Sum, FloatField
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .serializers import OrderDetailSerializer, OrderSerializer, OrderTransactionSerializer


class OrdersView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    queryset = Order.objects.prefetch_related('classes', 'order_transactions')
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = OrderDetailSerializer(instance)
        return Response(serializer.data)

    def transactions(self, request, *args, **kwargs):
        instance = self.get_object()
        queryset = instance.order_transactions.select_related('user_class', 'payment_type', 'student', 'instructor').prefetch_related('transaction_coupons', 'user_class__course', 'refund_requests').all()
        serializer = OrderTransactionSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def count_by_date_orders(self, request, *args, **kwargs):
        current_start, current_end = arrow.utcnow().span('month')
        last_start, last_end = arrow.now().shift(months=-1).span('month')

        startDate = request.GET.get('from')
        endDate = request.GET.get('to')
        if not startDate or not endDate:
            startDate = current_start
            endDate = current_end
        else:
            startDate = arrow.get(startDate)
            endDate = arrow.get(endDate)
            last_start, last_end = startDate.shift(months=-1).span('month')
        # Make query to get count of orders
        context = dict()
        context['total_orders'] = Order.objects.filter(Q(date_created__date__gte=startDate.date()) & Q(date_created__date__lte=endDate.date()) & Q(refund = False)).count()
        context['last_month_orders'] = Order.objects.filter(Q(date_created__date__gte=last_start.date()) & Q(date_created__date__lte=last_end.date())).count()
        
        # Make query to get sale price of orders
        
        sale_prices = Order.objects.filter(Q(date_created__date__gte=startDate.date()) & Q(date_created__date__lte=endDate.date()) & Q(refund = False) & ~Q(order_transactions__type=TransactionTypes.PAYOUT))\
            .prefetch_related('order_transactions').aggregate(total_sales=Coalesce(Sum('order_transactions__gross_amount'), 0, output_field=FloatField()))
        context.update(sale_prices)
        
        last_month_sale_price = Order.objects.filter(Q(date_created__date__gte=last_start.date()) & Q(date_created__date__lte=last_end.date()) & Q(refund = False) & ~Q(order_transactions__type=TransactionTypes.PAYOUT))\
            .prefetch_related('order_transactions').aggregate(last_month_sale_prices=Coalesce(Sum('order_transactions__gross_amount'), 0, output_field=FloatField()))
        context.update(last_month_sale_price)
       
        #make query to get sale price by location
        context['sales_by_location'] = Country.objects.prefetch_related('currency', 'currency__transactions').exclude(currency=None).filter(~Q(currency__transactions__type=TransactionTypes.PAYOUT)).values('name').\
            annotate(total_price=Sum('currency__transactions__gross_amount'), \
                total_transaction=Count('currency__transactions')).\
                    exclude(total_transaction=0).values('name', 'total_price', 'total_transaction')
        
        order_values = Order.objects.prefetch_related('order_transactions').filter(Q(date_created__date__gte=startDate.date()) & Q(date_created__date__lte=endDate.date())).exclude(order_transactions=None).order_by('order_transactions__gross_amount')
        if order_values.exists():
            minimun_order_value = order_values.first().order_transactions.first().gross_amount
            maximum_order_value = order_values.last().order_transactions.first().gross_amount
            average_value = order_values.aggregate(average_value=Coalesce(Avg('order_transactions__gross_amount'), 0, output_field=FloatField()))
            context['average_order_value'] = {
                'average_value': average_value.get('average_value'),
                'minimun_value': minimun_order_value,
                'maximum_value': maximum_order_value
            }
        return Response(context)

    