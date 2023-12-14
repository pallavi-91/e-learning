from django.utils.functional import cached_property
from django.db import models
from django.contrib.auth import get_user_model
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.status import *

class InstructorPayouts(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'payouts'
        
    period = models.DateField(editable=True)
    user = models.ForeignKey(get_user_model(), verbose_name='Instructor', related_name="payout_transactions", on_delete=models.CASCADE)
    status = models.CharField(max_length=15, choices=PayoutStatus.choices, default=PayoutStatus.PENDING)
    payout_type = models.CharField(max_length=20, default=PayoutType.ONGOING, choices=PayoutType.choices)
    
    paid_at = models.DateTimeField(editable=True, blank=True, null=True)
    due_date = models.DateField(editable=True, blank=True, null=True)
    
    def __str__(self) -> str:
        return f"<InstructorPayouts> {self.id}"


class TransactionPayout(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'payouts_transactions'
        constraints = [
            models.UniqueConstraint(fields=['payout', 'transaction'], name='per_transaction_payout_constraint')
        ]
        
    payout = models.ForeignKey(InstructorPayouts, related_name="transactions", on_delete=models.CASCADE)
    transaction = models.ForeignKey("Transactions", related_name="transaction_payout", on_delete=models.CASCADE)
    
    def __str__(self) -> str:
        return f"<TransactionPayout> {self.id}"
    
    
class HoldTransaction(AutoCreatedUpdatedMixin):
    class Meta:
        db_table = 'payout_hold_transactions'
        constraints = [
            models.UniqueConstraint(fields=['status', 'transaction'], name='hold_transaction_status_constraint')
        ]
    transaction = models.ForeignKey("Transactions", related_name="hold", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), verbose_name='Hold By', related_name="hold_transactions", on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=HoldTransactionStatus.choices, default=HoldTransactionStatus.HOLD)
    
    
    def __str__(self) -> str:
        return f"<HoldTransaction> {self.id}"


class PayoutDirectTransition(AutoCreatedUpdatedMixin):
    """
        Approved the payout for direct payment
    """
    class Meta:
        db_table = 'payouts_direct_pay'
        constraints = [
            models.UniqueConstraint(fields=['status', 'payout'], name='direct_payout_status_constraint')
        ]
        
    payout = models.ForeignKey(InstructorPayouts, related_name="direct_transitions", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), verbose_name='Performed By', related_name="payout_transition", on_delete=models.CASCADE)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=PayoutTransitionStatus.choices, default=PayoutTransitionStatus.MARK_AS_PAID)
    
    
    def __str__(self) -> str:
        return f"<PayoutDirectTransition> {self.id}"