from apps.status.mixins import AutoCreatedUpdatedMixin
from django.db import models


class PayoutBatch(AutoCreatedUpdatedMixin):
    """ payout batch transaction logs
    """
    class Meta:
        db_table = 'batch_payouts'
        
    raw = models.JSONField(null=True)
    batch_id = models.CharField(max_length=100)
    status = models.CharField(max_length=50, null=True, blank=True)

    

    def __str__(self):
        return f"{self.batch_id}"