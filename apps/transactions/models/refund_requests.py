from django.utils.functional import cached_property
from django.db import models
from apps.transactions.utility import get_transaction_code
from apps.utils.paypal.checkout import PaypalOrder
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from django.utils.timezone import localtime
from django.db.transaction import atomic
from copy import deepcopy
from apps.status.mixins import AutoCreatedUpdatedMixin
from apps.status import *

class RefundRequest(AutoCreatedUpdatedMixin):
    """
        Transaction refund requests
    """
    class Meta:
        db_table = 'refund_requests'
        
    status = models.CharField(max_length=15, choices=RefundStatus.choices, default=RefundStatus.REFUND_PENDING)
    user = models.ForeignKey(get_user_model(),related_name='refund_requests',on_delete=models.CASCADE)
    reason = models.TextField()
    transaction = models.ForeignKey("Transactions", related_name='refund_requests',on_delete=models.CASCADE)
    refund_amount = models.FloatField(default=0)
    refund_type = models.CharField(max_length=20, default=RefundType.REGULAR, choices=RefundType.choices)
    

    def __str__(self) -> str:
        return f'<RefundRequest> {self.id}'

    @atomic
    def approve(self):
        if not self.transaction.order: return
        self.status = RefundStatus.REFUND_APPROVED

        # self.transaction.refund = True
        # self.transaction.date_refunded = localtime()
        # self.transaction.refund_status = RefundStatus.REFUND_APPROVED
        # self.transaction.save()

        user_class = self.transaction.user_class
        user_class.is_purchased = False
        user_class.save()
        user_class.transactions.update(refund=True, date_refunded = localtime(), refund_status = RefundStatus.REFUND_APPROVED)
        # Update all transation status to refund
        
        refund_transaction = deepcopy(self.transaction)
        refund_transaction.pk = None
        if self.refund_amount:
            refund_transaction.gross_amount = self.refund_amount

        refund_transaction.payout_status = PayoutStatus.REFUNDED
        refund_transaction.type = TransactionTypes.REFUND
        refund_transaction.transaction_id = get_transaction_code()
        refund_transaction.save()
        # TODO: trigger paypal refund process and update `transaction_id`
        self.save()
        return self

    @atomic
    def reject(self):
        self.status = RefundStatus.REFUND_REJECTED
        self.transaction.refund_status = RefundStatus.REFUND_REJECTED
        self.transaction.save()
        self.save()
        return self
