import pdb
from rest_framework.permissions import IsAdminUser
from rest_framework import  viewsets
from apps import status
from apps.apis.admin.paginations import CommonPagination
from apps.apis.admin.sales.payouts.filters import PayoutsFilter
from django.shortcuts import get_object_or_404
from apps.apis.admin.sales.query import channel_key_value
from apps.status import HoldTransactionStatus, PaymentMethods, PayoutPayStatus, PayoutTransitionStatus, PayoutType, TransactionStatus, TransactionTypes
from .serializers import AddHoldTransactionSerializer, HoldTransactionSerializer, InactivePayoutDetailSerializer, PaidPayoutDetailSerializer, PayoutHoldTransactionSerializer, PayoutSerializer, PayoutTransactionSerializer
from apps.transactions.models import HoldTransaction, InstructorPayouts, PayoutStatus,PaymentType,  SupportedGateway, TransactionPayout, Transactions
from rest_framework.response import Response
from django.db.models import Case, Count, F, Sum, When, FloatField, Value, Q, Max, Subquery, OuterRef, Exists
from django.db.models.functions import Coalesce, Round
from django.db.models.functions import TruncMonth, TruncDate
import arrow
from collections import defaultdict
from django_filters import rest_framework as filters
from rest_framework.exceptions import APIException, NotFound, ValidationError
from apps.transactions.tasks import add_paid_payout_transactions

class PayoutView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = PayoutSerializer
    pagination_class = CommonPagination
    queryset = InstructorPayouts.objects.select_related('user').prefetch_related('transactions', 'transactions__transaction').all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class  = PayoutsFilter
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # page = self.paginate_queryset(queryset)
        # if page is not None:
        #     serializer = self.get_serializer(page, many=True)
        #     return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def ongoing_payout_summery(self, request, *args, **kwargs):
        """
        Will be used in Payout dashboard card view and on OnGoing Payouts
        """
        current_start, current_end = arrow.utcnow().span('month')
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        ongoing_payout = InstructorPayouts.objects.prefetch_related('transactions').filter(payout_type = PayoutType.ONGOING).aggregate(
                                            payees = Count('user', distinct=True),
                                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=False)  & Q(transactions__transaction__type=TransactionTypes.SALE),
                                                            then=self._instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True)  & Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            bank_balance=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__payment_type=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            paypal_balance=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__payment_type__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            bank_payment=Coalesce(Round(Sum(Case(
                                                        When( Q(user__instructor__payout_method=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            paypal_payment=Coalesce(Round(Sum(Case(
                                                        When( Q(user__instructor__payout_method__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
                                        )
        ongoing_payout["period"] = current_start.format('MMMM YYYY')
        ongoing_payout["due_date"] = current_end.shift(months=+1).shift(days=+3).format('YYYY-MM-DD')
        
        return Response(ongoing_payout)
        
    def upcoming_dashboard_payout_summery(self, request, *args, **kwargs):
        """
        Will be used in Payout dashboard card view and on UpComing Payouts
        """
        # Upcoming payout
        last_start, last_end = arrow.now().shift(months=-1).span('month')
        
        upcoming_payout = InstructorPayouts.objects.prefetch_related('transactions').filter(period = last_start.date()).aggregate(
                                            payees = Count('user', distinct=True),
                                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=False)  & Q(transactions__transaction__type=TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True) & Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                                    )
        upcoming_payout["period"] = last_start.format('MMMM YYYY')
        upcoming_payout["due_date"] = last_end.shift(months=+1).shift(days=+3).format('YYYY-MM-DD')
        
        return Response(upcoming_payout)
    
    def dashboard_data_summery(self, request, *args, **kwargs):
        """
        Will be used in dashboard card data
        """
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        context = InstructorPayouts.objects.prefetch_related('transactions').aggregate(
            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.PAYOUT)),
            failed_payouts = Count(
                                Case(
                                        When(status = PayoutStatus.FAILED, then='id'),
                                    ), distinct=True
                                ),
            inactive_payout = Count(
                                Case(
                                        When(payout_type=PayoutType.INACTIVE, then='id'),
                                    ),
                                ),
            upcoming_payout = Count(
                                Case(
                                        When(payout_type=PayoutType.UPCOMING, then='id'),
                                    ),
                                distinct=True
                                ),
            bank_transfer=Coalesce(Round(Sum(Case(
                                        When( Q(user__instructor__payout_method=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.PAYOUT),  #needs to discuss 
                                            then=F('transactions__transaction__gross_amount')
                                    ), default=0, output_field=FloatField()
                                    ))), Value(0), output_field=FloatField()),
            paypal_transafer=Coalesce(Round(Sum(Case(
                                        When( Q(user__instructor__payout_method__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.PAYOUT), 
                                            then=F('transactions__transaction__gross_amount')
                                    ), default=0, output_field=FloatField()
                                    ))), Value(0), output_field=FloatField()),
        )
        
        return Response(context)
    
    def upcoming_payout_summery(self, request, *args, **kwargs):
        """
        Will be used in Upcoming Payouts sections
        
        bank_balance, paypal_labance is the amount that are received.
        bank_payment, paypal_payment is the amount that have to Transfer to instructor
        """
        # Upcoming payout
        last_start, last_end = arrow.now().shift(months=-1).span('month')
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        payout_type = request.query_params.get('type', PayoutType.UPCOMING)
        upcoming_payout = InstructorPayouts.objects.prefetch_related('transactions').filter(payout_type = payout_type).aggregate(
                                            payees = Count('user', distinct=True),
                                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When(  Q(transactions__transaction__refund=False)  & Q(transactions__transaction__type=TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True) & Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            bank_balance=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__payment_type=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            paypal_balance=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__payment_type__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            bank_payment=Coalesce(Round(Sum(Case(
                                                        When( Q(user__instructor__payout_method=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            paypal_payment=Coalesce(Round(Sum(Case(
                                                        When( Q(user__instructor__payout_method__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                            then=self._instructor_share_amount()
                                                    ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
                                        )
        upcoming_payout["period"] = last_start.format('YYYY-MM-DD')
        upcoming_payout["due_date"] = last_end.shift(months=+1).shift(days=+3).format('YYYY-MM-DD')
        
        return Response(upcoming_payout)
    
    
    def failed_payouts_summery(self, request, *args, **kwargs):
        """
        Will be used in Failed Payouts sections
        """
        context_payout = InstructorPayouts.objects.prefetch_related('transactions').filter(payout_type = PayoutType.FAILED).aggregate(
                                            failed_payouts = Count('id', distinct=True),
                                            total_earnings=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=False) & Q(transactions__transaction__type=TransactionTypes.SALE), 
                                                            then='transactions__transaction__gross_amount'
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True) & Q(transactions__transaction__type=TransactionTypes.SALE),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
                                        )
        return Response(context_payout)
      
    def _instructor_share_amount(self):
        return (
                    F('transactions__transaction__gross_amount') - (
                        F('transactions__transaction__gateway_charge') + F('transactions__transaction__vat_amount') 
                    ) 
                )* (channel_key_value('instructor_share', 'transactions__transaction__channel')/100)
        
    
    def payout_detail_summery(self, request, *args, **kwargs):
        """
            Payout details with transactions summery
        """
        instance = get_object_or_404(InstructorPayouts, **kwargs)
        serializer = PaidPayoutDetailSerializer(instance).data
        return Response(serializer) 
    
    def payout_transactions(self, request, *args, **kwargs):
        """
            Payout details transactions list
        """
        try:
            instance = get_object_or_404(InstructorPayouts, **kwargs)
            params = request.query_params
            queryset = instance.transactions.select_related('transaction').prefetch_related('transaction__payment_type', 'transaction__hold')
            last_hold_transaction = HoldTransaction.objects.filter(transaction=OuterRef('transaction')).order_by('-id').values('status')[:1]
            if params.get('hold', False) == 'true':
                queryset = queryset.annotate(hold_status=Subquery(last_hold_transaction)).filter(hold_status=HoldTransactionStatus.HOLD)
            else:
                queryset = queryset.annotate(hold_status=Subquery(last_hold_transaction)).filter(Q(hold_status=None)|Q(hold_status=HoldTransactionStatus.UNHOLD))
            serializer = PayoutTransactionSerializer(queryset, many=True).data
            return Response(serializer)
        except Exception as ex:
            raise APIException(ex)

    def unhold_transaction(self, request, *args, **kwargs):
        hold_transactions = HoldTransaction.objects.filter(id=kwargs.get('tid'))
        if hold_transactions.exists():
            instructor_payout = get_object_or_404(InstructorPayouts, id=kwargs.get('id'))
            
            hold_transactions.update(status=HoldTransactionStatus.UNHOLD, user=request.user)
            if instructor_payout.payout_type != PayoutType.ONGOING:
                upcoming_payouts = InstructorPayouts.objects.filter(payout_type=PayoutType.UPCOMING, user=instructor_payout.user)
                if not upcoming_payouts.exists():
                    raise NotFound('No Upcoming payout for this instructor')
                upcoming_payout = upcoming_payouts.last()
                for trans in hold_transactions:
                    # Move the hold transaction to upcoming payout of the same instructor
                    trans.transaction.transaction_payout.all().update(payout=upcoming_payout)
            serializer = HoldTransactionSerializer(hold_transactions, many=True).data
            return Response(serializer)
        return Response(data={'details': 'Hold transaction not found'}, status=404)
    
    
    
    
    
    def hold_transaction(self, request, *args, **kwargs):
        transaction = get_object_or_404(Transactions, id=kwargs.get('tid'))
        holds = transaction.hold.filter(status=HoldTransactionStatus.HOLD) 
        if holds.count():
            serializer_data = HoldTransactionSerializer(holds.last()).data
            return Response(serializer_data)
        payload = dict()
        payload['transaction'] = transaction.id
        payload['reason'] = request.data.get('reason', '')
        payload['user'] = request.user.id
        payload['status'] = HoldTransactionStatus.HOLD
        serializer = AddHoldTransactionSerializer(data=payload)
        if serializer.is_valid():
            instance = serializer.save()
            serializer_data = HoldTransactionSerializer(instance).data
            return Response(serializer_data)
        raise ValidationError(serializer.errors)

    def mark_ready(self, request, *args, **kwargs):
        payouts = request.data.get('payouts', [])
        instructor_payouts = InstructorPayouts.objects.filter(Q(id__in=payouts)& ~Q(status=PayoutStatus.SUCCESS))
        instructor_payouts.update(status=PayoutStatus.READY)
        serializer = PayoutSerializer(instructor_payouts, many=True).data
        return Response(serializer, status=200)
    
    def mark_paid(self, request, id, *args, **kwargs):
        instructor_payouts = InstructorPayouts.objects.filter(Q(id=id))
        instructor_payouts.update(status=PayoutStatus.SUCCESS, payout_type=PayoutType.PAID)
        serializer = PayoutSerializer(instructor_payouts, many=True).data
        # Add a new transaction on the orders and classes
        add_paid_payout_transactions(id, action=PayoutTransitionStatus.MARK_AS_PAID, user=request.user.id)
        return Response(serializer, status=200)
    
    def mark_activated(self, request, *args, **kwargs):
        payouts = request.data.get('payouts', [])
        instructor_payouts = InstructorPayouts.objects.filter(Q(id__in=payouts))
        instructor_payouts.update(status=PayoutStatus.PENDING, payout_type=PayoutType.PAID)
        serializer = PayoutSerializer(instructor_payouts, many=True).data
        for id in payouts:
            add_paid_payout_transactions(id, action=PayoutTransitionStatus.INACTIVE_PAID, user=request.user.id)
            
        return Response(serializer, status=200)
    
    def payout_hold_transactions(self, request, *args, **kwargs):
        """
            Payout hold details transactions list
        """
        try:
            queryset = HoldTransaction.objects.filter(status=HoldTransactionStatus.HOLD)
            serializer = PayoutHoldTransactionSerializer(queryset, many=True).data
            return Response(serializer)
        except Exception as ex:
            raise APIException(ex)


class PaidPayoutView(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = PayoutSerializer
    pagination_class = CommonPagination
    queryset = InstructorPayouts.objects.select_related('user').prefetch_related('transactions', 'transactions__transaction').all()
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class  = PayoutsFilter
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    
    def paid_payout_summery(self, request, *args, **kwargs):
        """
        Will be used in Payout dashborad
        """
        # Latest Paid Payouts
        last_start, last_end = arrow.now().shift(months=-2).span('month')
        period = last_start.date()
        paid_payout = InstructorPayouts.objects.prefetch_related('transactions').filter(period=period).aggregate(
                                            payees = Count('user', distinct=True),
                                            paid_payees = Count(
                                                    Case(
                                                            When(status = PayoutStatus.SUCCESS, then='user'),
                                                        ), distinct=True
                                                    ),
                                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( status = PayoutStatus.SUCCESS, 
                                                            then=self._instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True) & Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            )
        paid_payout.update({'period': last_start.format('MMMM YYYY')})
        return Response(paid_payout)
    
    def _instructor_share_amount(self):
        return (
                    F('transactions__transaction__gross_amount') - (
                        F('transactions__transaction__gateway_charge') + F('transactions__transaction__vat_amount') 
                    ) 
                )* (channel_key_value('instructor_share', 'transactions__transaction__channel')/100)
    
    def paid_payout_periods(self, request, *args, **kwargs):
        """
        Will be used in Payout Paid Period table (dashboard data).
        """
        # Platform based pariodic data
        last_start, _ = arrow.now().shift(months=-1).span('month')
        querysets = InstructorPayouts.objects.prefetch_related('transactions').filter(period__lt=last_start.date()).exclude(paid_at=None).values('period').annotate(
            payees = Count('user', distinct=True),
            success_payouts = Count(
                                    Case(
                                            When(status = PayoutStatus.SUCCESS, then='id'),
                                        ), distinct=True
                                    ),
            failed_payouts = Count(
                                Case(
                                        When(status = PayoutStatus.FAILED, then='id'),
                                    ), distinct=True
                                ),
            payout_amount=Coalesce(Round(Sum(Case(
                                                When(status = PayoutStatus.SUCCESS, 
                                                    then=self._instructor_share_amount()
                                                    ),
                                                default=0,
                                                output_field=FloatField()
                                            ))), Value(0), output_field=FloatField()),
            refund_amount=Coalesce(Round(Sum(Case(
                                                When(Q(transactions__transaction__refund=True) &  Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                    then=(F('transactions__transaction__gross_amount'))), 
                                                default=0, 
                                                output_field=FloatField()
                                            ))), Value(0), output_field=FloatField()),
        )
        try:
            limit = request.query_params.get('limit', False)
            if limit != False:
                querysets = querysets[:int(limit)]
        except Exception as ex:
            print(ex)
      
        data = querysets.values('period','success_payouts','failed_payouts','payout_amount','refund_amount', 'payees').annotate(
            status=Case( 
                        When( (Q(success_payouts__gt=0)&Q(payees__gt=F('success_payouts'))),
                            then=Value(PayoutPayStatus.PARTIAL)),
                        When( (Q(payees=F('success_payouts'))),
                            then=Value(PayoutPayStatus.FULL)),
                        When( (Q(failed_payouts=0)&Q(success_payouts=0)),
                            then=Value(PayoutPayStatus.UNPAID)),
                        default=Value(PayoutPayStatus.BLANK)
                    )
        ).values('period','success_payouts','failed_payouts','payout_amount','refund_amount', 'payees', 'status')
        return Response(data)
    
    def paid_payout_consolidated_history(self, request, *args, **kwargs):
        """
        Will be used in Paid Payout Period
        """
        # Latest Paid Payouts
        last_start, last_end = arrow.now().shift(months=-2).span('month')
        period = last_start.date()
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        
        queryset = InstructorPayouts.objects.prefetch_related('transactions', 'transactions__transaction__hold').filter(period=period)
        paid_payout = queryset.aggregate(payees = Count('user', distinct=True),
                                            success_payouts = Count(
                                                                    Case(
                                                                            When(status = PayoutStatus.SUCCESS, then='id'),
                                                                        ), distinct=True
                                                                    ),
                                            failed_payouts = Count(
                                                                Case(
                                                                        When(status = PayoutStatus.FAILED, then='id'),
                                                                    ), distinct=True
                                                                ),
                                            payout_amount=Coalesce(Round(Sum(Case(
                                                        When( status = PayoutStatus.SUCCESS, 
                                                            then=self._instructor_share_amount()
                                                            ),
                                                        default=0,
                                                        output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            refund_amount=Coalesce(Round(Sum(Case(
                                                        When( Q(transactions__transaction__refund=True) &  Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                            then=(F('transactions__transaction__gross_amount'))), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            hold_amount=Coalesce(Round(Sum(Case(
                                                        When( transactions__transaction__hold__status=HoldTransactionStatus.HOLD,
                                                            then=self._instructor_share_amount()
                                                            ), default=0, output_field=FloatField()
                                                    ))), Value(0), output_field=FloatField()),
                                            
                                            bank_transfer=Coalesce(Round(Sum(Case(
                                                                When( Q(user__instructor__payout_method=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                                    then=self._instructor_share_amount()
                                                            ), default=0, output_field=FloatField()
                                                            ))), Value(0), output_field=FloatField()),
                                            paypal_transafer=Coalesce(Round(Sum(Case(
                                                                When( Q(user__instructor__payout_method__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                                    then=self._instructor_share_amount()
                                                            ), default=0, output_field=FloatField()
                                                            ))), Value(0), output_field=FloatField()),
                                            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
                                        )
        paid_payout.update({'period': last_start.format('MMMM YYYY')})
        return Response(paid_payout)
    
    def paid_payout_detail_summery(self, request, period, *args, **kwargs):
        """
            Paid pariod details summery
        """
        
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        last_start = arrow.get(period)
        queryset = InstructorPayouts.objects.filter(period=last_start.date()).exclude(paid_at=None).prefetch_related('transactions', 'transactions__transaction__hold').values('period')
        paid_payout = queryset.aggregate(paid_date=Max('paid_at'),
                                        failed_amount = Coalesce(Round(Sum(Case(
                                                            When( status = PayoutStatus.FAILED, 
                                                                then=self._instructor_share_amount()
                                                                ),
                                                            default=0,
                                                            output_field=FloatField()
                                                        ))), Value(0), output_field=FloatField()),
                                        payees = Count('user', distinct=True),
                                        payout_amount=Coalesce(Round(Sum(Case(
                                                    When( status = PayoutStatus.SUCCESS, 
                                                        then=self._instructor_share_amount()
                                                        ),
                                                    default=0,
                                                    output_field=FloatField()
                                                ))), Value(0), output_field=FloatField()),
                                        
                                        hold_amount=Coalesce(Round(Sum(Case(
                                                    When( transactions__transaction__hold__status=HoldTransactionStatus.HOLD,
                                                        then=self._instructor_share_amount()
                                                        ), default=0, output_field=FloatField()
                                                ))), Value(0), output_field=FloatField()),
                                        
                                        bank_transfer=Coalesce(Round(Sum(Case(
                                                            When( Q(user__instructor__payout_method=payment_method_bank) & Q(transactions__transaction__type = TransactionTypes.SALE),  #needs to discuss 
                                                                then=self._instructor_share_amount()
                                                        ), default=0, output_field=FloatField()
                                                        ))), Value(0), output_field=FloatField()),
                                        paypal_transafer=Coalesce(Round(Sum(Case(
                                                            When( Q(user__instructor__payout_method__in=payment_method_paypal) & Q(transactions__transaction__type = TransactionTypes.SALE), 
                                                                then=self._instructor_share_amount()
                                                        ), default=0, output_field=FloatField()
                                                        ))), Value(0), output_field=FloatField()),
                                        total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
                                    )
        return Response(paid_payout)
    
    def instructor_paid_detail(self, request, *args, **kwargs):
        """
        Will be used on payout dashboard stock chart data
        """
        data = InstructorPayouts.objects.filter(payout_type=PayoutType.PAID).prefetch_related('transactions')\
        .annotate(date=TruncDate('date_updated'))\
        .values('date')\
        .annotate(
                    payout_amount=Coalesce(Round(Sum(Case(
                                                When(status = PayoutStatus.SUCCESS, 
                                                    then=self._instructor_share_amount()
                                                    ),
                                                default=0,
                                                output_field=FloatField()
                                            ))), Value(0), output_field=FloatField()),
                    ).values('payout_amount','date')
        
        return Response(data)
    

    def inactive_payout_consolidated_history(self, request, *args, **kwargs):
        """
        Will be used in Inactive Payout Period
        """
        instance = get_object_or_404(InstructorPayouts, **kwargs)
        payment_method_bank = PaymentType.objects.get(payment_gateway=SupportedGateway.HYPERPAY, payment_method=PaymentMethods.BANK_TRANSFER)
        payment_method_paypal = PaymentType.objects.filter(payment_gateway=SupportedGateway.PAYPAL)
        context = {
            'bank_transfer': payment_method_bank,
            'paypal_transfer': payment_method_paypal
        }
        serializer = InactivePayoutDetailSerializer(instance, context=context)
        return Response(serializer.data)
    
    def retry_failed_payout(self, request, *args, **kwargs):
        instructor_payout = get_object_or_404(InstructorPayouts, id=kwargs.get('id'))

        if instructor_payout.payout_type != PayoutType.FAILED:
            return Response(data={'details': 'Payout is not valid for retry'}, status=406)
        else:
            upcoming_payouts = InstructorPayouts.objects.filter(payout_type=PayoutType.UPCOMING, user=instructor_payout.user)
            if not upcoming_payouts.exists():
                raise NotFound('No upcoming payout for this instructor found')
            upcoming_payout = upcoming_payouts.last()
            payout_transactions = instructor_payout.transactions.select_related('transaction').filter(transaction__payout_status=PayoutStatus.FAILED)
            payout_transactions.update(payout=upcoming_payout)
            # Change the failed payout status of assigned transactions
            
        return Response(status=200)
    
    
    def retry_all_failed_payout(self, request, period, *args, **kwargs):
        failed_payouts = InstructorPayouts.objects.filter(payout_type=PayoutType.FAILED, period=period)
        if not failed_payouts.exists():
            return Response(data={'details': 'Payout is not available.'}, status=406)
        else:
            for instructor_payout in failed_payouts:
                upcoming_payouts = InstructorPayouts.objects.filter(payout_type=PayoutType.UPCOMING, user=instructor_payout.user)
                if upcoming_payouts.exists():
                    upcoming_payout = upcoming_payouts.last()
                    payout_transactions = instructor_payout.transactions.select_related('transaction').filter(transaction__payout_status=PayoutStatus.FAILED)
                    payout_transactions.update(payout=upcoming_payout)
                    # Change the failed payout status of assigned transactions
                    transaction_id = upcoming_payout.transactions.select_related('transaction').values_list('transaction', flat=True)
                    transactions = Transactions.objects.filter(id__in=transaction_id)
                    transactions.update(payout_status='', payout_error={})
                    
        return Response(status=200)
    
    def failed_payout_periods(self, request, *args, **kwargs):
        """
        Will be used in Failed Payout Period table
        """
        querysets = InstructorPayouts.objects.prefetch_related('transactions').filter(payout_type=PayoutType.FAILED).values('period').annotate(
            payees = Count('id', distinct=True),
            payout_amount=Coalesce(Round(Sum(Case(
                                                When(Q(transactions__transaction__refund=False) &  Q(transactions__transaction__type=TransactionTypes.SALE), 
                                                    then=self._instructor_share_amount()
                                                    ),
                                                default=0,
                                                output_field=FloatField()
                                            ))), Value(0), output_field=FloatField()),
            refund_amount=Coalesce(Round(Sum(Case(
                                                When( Q(transactions__transaction__refund=True) &  Q(transactions__transaction__type=TransactionTypes.REFUND),
                                                    then=(F('transactions__transaction__gross_amount'))), 
                                                default=0, 
                                                output_field=FloatField()
                                            ))), Value(0), output_field=FloatField()),
            ready_payout=Count('id', filter=Q( status = PayoutStatus.READY), distinct=True),
            total_transactions=Count('transactions__transaction__id', filter=Q(transactions__transaction__type=TransactionTypes.SALE)),
            hold_amount=Coalesce(Round(Sum(Case(
                                                    When( transactions__transaction__hold__status=HoldTransactionStatus.HOLD,
                                                        then=self._instructor_share_amount()
                                                        ), default=0, output_field=FloatField()
                                                ))), Value(0), output_field=FloatField()),
        )
        try:
            limit = request.query_params.get('limit', False)
            if limit != False:
                querysets = querysets[:int(limit)]
        except Exception as ex:
            print(ex)
      
        data = querysets.values('period','ready_payout','total_transactions', 'hold_amount', 'payout_amount','refund_amount', 'payees')
        new_records = defaultdict(list)
        for item in data:
            date = item['period'].strftime('%B %Y')
            new_records[date].append(item)
        return Response(new_records)