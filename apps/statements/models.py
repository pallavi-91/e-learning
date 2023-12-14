import pdb
from django.db import models
from apps.status import RefundStatus, StatementEventTypes, StatementStatus
from apps.transactions.models import PaymentType, TransactionTypes
from types import SimpleNamespace
from django.utils.functional import cached_property
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.users.models import UserClass

# Create your models here.

class StatementQuerySet(models.QuerySet):
    def for_instructor(self, user):
        return self.prefetch_related('statements').filter(statements__transaction_detail__instructor=user.id)
    
    def of_platform(self):
        return self.prefetch_related('statements').exclude(statements__transaction_detail__type=TransactionTypes.SALE)
    
        
class Statement(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'statements'
        verbose_name = 'Statement'
        verbose_name_plural = 'Statements'
        ordering = ['-date_created']
        
    period = models.CharField(max_length=20, unique = True)
    status = models.CharField(max_length=100, choices=StatementStatus.choices, default=StatementStatus.CURRENT)
    start_date = models.DateField(blank=True, null=True)
    end_date  = models.DateField(blank=True, null=True)
    
    
    objects = StatementQuerySet.as_manager()
    
    def __str__(self) -> str:
        return f"<Statement> {self.period}"

class StatementTransactionQuerySet(models.QuerySet):
    def for_instructor(self, user):
        return self.filter(transaction_detail__instructor=user.id)
    
    def of_platform(self):
        return self.exclude(transaction_detail__type=TransactionTypes.SALE)
    
class StatementTransactions(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'statements_transaction'
        verbose_name = 'Transaction Statement'
        verbose_name_plural = 'Transaction Statements'
        ordering = ['-date_created']
        
    statement = models.ForeignKey(Statement,related_name="statements", on_delete=models.CASCADE)
    transaction_detail = models.JSONField(default=dict)
    objects = StatementTransactionQuerySet.as_manager()
    
    def __str__(self) -> str:
        return f"<StatementTransactions> {self.id}"
    
    @cached_property
    def transaction(self):
        if self.transaction_detail:
            return SimpleNamespace(**self.transaction_detail)
        return None
    
    @cached_property
    def payment_type(self):
        return SimpleNamespace(**self.transaction.payment_type)  
    
    @cached_property
    def net_amount(self):
        """ total amount after the deduction (amount that reflected to the merchant account)
        """
        if self.transaction.type == TransactionTypes.PAYOUT:
            return round(float(self.transaction.gross_amount), 2)

        return self.transaction.gross_amount - (self.payment_type.gateway_charge + self.transaction.vat_amount)
    
    @cached_property
    def instructor_fee(self):
        _fee = round((self.transaction.channel.get('instructor_share')/100),2)
        return round(self.net_amount * _fee, 2)
    
    @cached_property
    def platform_fee(self):
        _fee = round((self.transaction.channel.get('platform_share')/100),2)
        return round(self.net_amount * _fee, 2)
    
    @cached_property
    def refund_amount(self):
        if self.transaction.refund and self.transaction.type==TransactionTypes.REFUND:
            return round(self.transaction.gross_amount, 2)
        return 0
    
    @cached_property
    def listed_price(self):
        try:
            user_class = UserClass.objects.select_related('course').get(id=self.transaction.user_class)
            return user_class.price
        except:
            return 0
    
    @cached_property
    def event(self):
        if self.transaction.refund and self.transaction.refund_status != RefundStatus.REFUND_CHARGEBACK:
            return StatementEventTypes.REFUND
        elif self.transaction.refund and self.transaction.refund_status == RefundStatus.REFUND_CHARGEBACK:
            return StatementEventTypes.CHARGEBACK
        elif self.transaction.refund and self.transaction.refund_status == RefundStatus.REFUND_RECONCILE:
            return StatementEventTypes.RECONCILATION
        else:
            return StatementEventTypes.EARNINGS