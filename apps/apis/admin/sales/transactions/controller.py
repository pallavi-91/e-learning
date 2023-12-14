import pdb
from rest_framework.permissions import IsAdminUser
from rest_framework import  viewsets
import arrow
from apps.statements.models import Statement
from apps.status import HoldTransactionStatus, PayoutType, RefundStatus, TransactionStatus
from apps.users.models import Instructor, Order
from .serializers import TransactionDetailSerializer, TransactionInvoiceSerializer, TransactionSerializer
from apps.transactions.models import HoldTransaction, InstructorPayouts, RefundRequest, Transactions, TransactionTypes
from rest_framework.response import Response
from django.db.models import Avg, Case, Count, F, Func, Max, Min, Prefetch, Q, Sum, When, FloatField, Value
from django.db.models.functions import Coalesce, TruncDate, Round, Cast
from django.db.models.expressions import Value
from apps.apis.admin.sales.query import instructor_share, platform_share, affiliate_share
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class TransactionView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = TransactionSerializer
    queryset = Transactions.objects.select_related('user_class', 'payment_type', 'student', 'instructor').prefetch_related('transaction_coupons', 'user_class__course').sales_transactions()
    
    # @method_decorator(cache_page(60))
    def dispatch(self, *args, **kwargs):
        return super(TransactionView, self).dispatch(*args, **kwargs)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TransactionDetailSerializer(instance)
        return Response(serializer.data)
    
    def invoice_detail(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = TransactionInvoiceSerializer(instance)
        return Response(serializer.data)
    
    def total_earnings(self, request, *args, **kwargs):
        """
        earnings": {
                "platform": 6.4,
                "affiliate": 6.4,
                "instructor": 6.4
            },
            "refund": 0,
            "chargeback": 0,
            "date_created": "2022-12-23"
        """
        if not all( k in ['from', 'to'] for k in request.query_params.keys()):
            return Response(status=400)
        
        context = dict()
        start_oty, end_oty = arrow.now().span('year')
        from_date = request.query_params.get('from', start_oty.date())
        to_date = request.query_params.get('to', end_oty.date())
        
        queryset = self.get_queryset().filter(Q(date_created__date__gte=from_date) & Q(date_created__date__lte=to_date))
        context['sales'] = queryset.annotate(date=TruncDate('date_updated')).values('date').annotate(sales=Coalesce(Sum('gross_amount'), Value(0), output_field=FloatField())).values('date', 'sales')
        context['total_sales'] = sum([i.get('sales') for i in context['sales'] ])
        
        context['earnings'] = queryset.aggregate(
                    total_earnings=Coalesce(Sum(Case(
                            When(Q(type=TransactionTypes.SALE) & Q(refund=False), 
                                then=(
                                        F('gross_amount') - (
                                                F('gateway_charge') + F('vat_amount') 
                                            ) 
                                    )
                                ),
                            default=0,
                            output_field=FloatField())
                        ), Value(0), output_field=FloatField()),
                    total_refund=Coalesce(Sum(Case(
                            When(Q(type=TransactionTypes.REFUND) & Q(refund=True), 
                                then=F('gross_amount')
                            ),
                            default=0,
                            output_field=FloatField())
                        ), Value(0), output_field=FloatField()),
                    total_chargebacks=Coalesce(Sum(Case(
                            When(Q(refund_status=RefundStatus.REFUND_CHARGEBACK) & Q(refund=True), 
                                then=F('gross_amount')
                            ),
                            default=0,
                            output_field=FloatField())
                        ), Value(0), output_field=FloatField()),
                        
                    thkee_earnings=Coalesce(Round(Sum(Case(
                            When(Q(type=TransactionTypes.SALE) & Q(refund=False), 
                                then=(
                                            F('gross_amount') - (
                                                F('gateway_charge') + F('vat_amount') 
                                            ) 
                                        )* (platform_share/100)
                                ),
                            default=0,
                            output_field=FloatField())
                        )), Value(0), output_field=FloatField()),
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
                    affiliate_earnings=Coalesce(Round(Sum(Case(
                            When(Q(type=TransactionTypes.SALE) & Q(refund=False), 
                                then=(
                                            F('gross_amount') - (
                                                F('gateway_charge') + F('vat_amount') 
                                            ) 
                                        )* (affiliate_share/100)
                                ),
                            default=0,
                            output_field=FloatField()
                        ) )), Value(0), output_field=FloatField()),
                )
        return Response(context)
        

    def ecommerce_summery(self, request, *args, **kwargs):
        context = dict()
        yesterday_date, _ = arrow.now().shift(days=-1).span('day')
        last_seven_day, _ = arrow.now().shift(days=-7).span('day')
        
        context['transactions'] = Transactions.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['statements'] = Statement.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['instructors'] = Instructor.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['instructor_statements'] = Statement.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['orders'] = Order.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['payout_success_paid'] = InstructorPayouts.objects.filter(payout_type=PayoutType.PAID).aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['failed_transactions'] = Transactions.objects.filter(status=TransactionStatus.FAILED).aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['hold_transactions'] = HoldTransaction.objects.filter(status=HoldTransactionStatus.HOLD).aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['refund_requests'] = RefundRequest.objects.aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        context['total_refunded'] = RefundRequest.objects.filter(status=RefundStatus.REFUND_SUCCESS).aggregate(total=Count('id'), 
                                       from_yesterday=Count(Case(
                                           When(date_created__date__gte= yesterday_date.date(), then='id')
                                           )),
                                       new=Count(Case(
                                           When(date_created__date__gte= last_seven_day.date(), then='id')
                                           )),
                                       )
        return Response(context)
    
    def transaction_receipt(self, request, *args, **kwargs):
        context = dict()
        instance = self.get_object()
        return Response(context)